// slider.js

let slideIndex = 0;
showSlides(slideIndex);

// Cambia la diapositiva actual al siguiente o anterior
function plusSlides(n) {
    showSlides(slideIndex += n);
}

// Muestra la diapositiva seleccionada
function currentSlide(n) {
    showSlides(slideIndex = n);
}

function showSlides(n) {
    const slides = document.getElementsByClassName("slide");
    if (slides.length === 0) return;

    // Asegura que el índice de la diapositiva está en el rango
    if (n >= slides.length) {
        slideIndex = 0;
    } else if (n < 0) {
        slideIndex = slides.length - 1;
    } else {
        slideIndex = n;
    }

    // Oculta todas las diapositivas
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }

    // Muestra la diapositiva actual
    slides[slideIndex].style.display = "block";
}
