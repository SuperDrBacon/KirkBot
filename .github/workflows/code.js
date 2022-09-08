'use strict';

// const themeSwitch = document.querySelector('.theme-switch');
// themeSwitch.checked = localStorage.getItem('switchedTheme') === 'true';
// const switcher = document.querySelector('.theme-button');

// switcher.addEventListener('click', function() {
//     document.body.classList.set('dark-theme');
//     document.body.classList.set('light-theme');
    
//     const className = document.body.className;
//     if(className == "light-theme") {
//         this.textContent = "Dark";
//     } else if (className == "dark-theme") {
//         this.textContent = "Light";
//     } else if (className == "") {
//         this.textContent = "Error";
//     }else {
//         this.textContent = "kut";
//     }
//     console.log('Current theme: ' + className);
// });

// function themeSwitcher() {
//     var element = document.getElementById("mainBody");
//     // const className = document.body.className;
//     if(element == "light-theme") {
//         this.textContent = "Dark";
//         document.body.classList.toggle("dark-theme");
//     } else if (element == "dark-theme") {
//         this.textContent = "Light";
//         document.body.classList.toggle("light-theme");
//     } else {
//         this.textContent = "dark";
//         document.body.classList.toggle("dark-theme");
//     }
// }

// function to set a given theme/color-scheme
function setTheme(themeName) {
    localStorage.setItem('theme', themeName);
    document.documentElement.className = themeName;
}
// function to toggle between light and dark theme
function toggleTheme() {
    if (localStorage.getItem('theme') === 'theme-dark'){
        setTheme('theme-light');
    } else {
        setTheme('theme-dark');
    }
}
// Immediately invoked function to set the theme on initial load
(function () {
    if (localStorage.getItem('theme') === 'theme-dark') {
        setTheme('theme-dark');
    } else {
        setTheme('theme-light');
    }
})();