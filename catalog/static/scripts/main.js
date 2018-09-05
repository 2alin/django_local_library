var menuButton = document.querySelector('div.menu');
var sideBar = document.querySelector('div.sidebar');

menuButton.addEventListener('click', () => {
    if(sideBar.classList.contains('show')) {
        sideBar.classList.remove('show');
        sideBar.classList.add('hide');
    } else {
        sideBar.classList.remove('hide');
        sideBar.classList.add('show')
    }
});