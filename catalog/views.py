from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre
from django.views import generic
# for loan books by User
from django.contrib.auth.mixins import LoginRequiredMixin
# to display all loaned books
from django.contrib.auth.mixins import PermissionRequiredMixin 
# for librarian renewing forms
import datetime

from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookForm


# for Author edit forms, available for admins
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Author



# Create your views here.

def index(request):
    """
    View function for home page of site.
    """
    # Generate counts of some of the main objects
    num_books=Book.objects.all().count()
    num_instances=BookInstance.objects.all().count()
    # Available books (status = 'a')
    num_instances_available=BookInstance.objects.filter(status__exact='a').count()
    num_authors=Author.objects.count() # The 'all()' is implied by default.

    # asked in the challenge guide section
    num_genres=Genre.objects.count()
    num_books_matching=Book.objects.filter(title__icontains='the').count() # case insensitive

    # Number of visits to this view, as counted in the session variable
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    context={
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_books_matching': num_books_matching,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 5

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 5

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LoanedBooksListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all books on loan"""
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    template_name = 'catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')
    

# for librarian renewing forms
@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required 
            # (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL
            return HttpResponseRedirect(reverse('all-borrowed'))
    
    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

# for Author edit forms, permissions required
class AuthorCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    fields = '__all__'
    #initial = {'date_of_death': '05/01/2018'}

    def form_valid(self, form):
        date_birth = form.cleaned_data['date_of_birth']
        date_death = form.cleaned_data['date_of_death']
        # check if birth date and death date are not set in the future 
        if date_birth > datetime.date.today():
            form.add_error('date_of_birth','Invalid date - no time lords are admitted')
            return self.form_invalid(form)
        if date_death > datetime.date.today():
            form.add_error('date_of_death','Invalid date - you can\'t see the future')
            return self.form_invalid(form)

        # Check if birth date and death date are not mixed up
        if date_birth > date_death:
            form.add_error('date_of_death','Invalid date - death comes after birth')
            return self.form_invalid(form)

        return super(AuthorCreate, self).form_valid(form)

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

    def form_valid(self, form):
        date_birth = form.cleaned_data['date_of_birth']
        date_death = form.cleaned_data['date_of_death']
        # check if birth date and death date are not set in the future 
        if date_birth > datetime.date.today():
            form.add_error('date_of_birth','Invalid date - no time lords are admitted')
            return self.form_invalid(form)
        if date_death > datetime.date.today():
            form.add_error('date_of_death','Invalid date - you can\'t see the future')
            return self.form_invalid(form)

        # Check if birth date and death date are not mixed up
        if date_birth > date_death:
            form.add_error('date_of_death','Invalid date - death comes after birth')
            return self.form_invalid(form)

        return super(AuthorUpdate, self).form_valid(form)


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    success_url = reverse_lazy('authors')

# for Book edit forms, permissions required
class BookCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = '__all__'

    def form_valid(self, form):
        data = form.cleaned_data['isbn']

        # check if isbn is a list of numbers 
        if not data.isdigit():
            form.add_error('isbn','Invalid ISBN - only numbers admitted')
            return self.form_invalid(form)

        # Check if isbn is 13 digits long
        if len(data) != 13:
            form.add_error('isbn','Invalid ISBN - it should be 13 digits long')
            return self.form_invalid(form)

        return super(BookCreate, self).form_valid(form)

class BookUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = '__all__'

    def form_valid(self, form):
        data = form.cleaned_data['isbn']

        # check if isbn is a list of numbers 
        if not data.isdigit():
            form.add_error('isbn','Invalid ISBN - only numbers admitted')
            return self.form_invalid(form)

        # Check if isbn is 13 digits long
        if len(data) != 13:
            form.add_error('isbn','Invalid ISBN - it should be 13 digits long')
            return self.form_invalid(form)

        return super(BookUpdate, self).form_valid(form)

class BookDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    success_url = reverse_lazy('books')