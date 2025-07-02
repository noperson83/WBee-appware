// Adjust nav sidebar on window resize to remove gaps
// Adds or removes the 'shifted' class on #main based on stored sidebar state.
document.addEventListener('DOMContentLoaded', function () {
  const main = document.getElementById('main');
  const navSidebar = document.getElementById('nav-sidebar');
  const toggle = document.getElementById('toggle-nav-sidebar');
  if (!main || !navSidebar || !toggle) return;
  function adjust() {
    if (window.innerWidth <= 767) {
      main.classList.remove('shifted');
    } else {
      const isOpen = localStorage.getItem('django.admin.navSidebarIsOpen');
      main.classList.toggle('shifted', isOpen === null || isOpen === 'true');
    }
  }
  window.addEventListener('resize', adjust);
  adjust();
});
