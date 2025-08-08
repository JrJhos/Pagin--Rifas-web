document.addEventListener('DOMContentLoaded', function() {
    const ticketGrid = document.getElementById('ticket-grid');
    const apartarSeccion = document.getElementById('apartar-seccion');
    const selectedTicketsList = document.getElementById('selected-tickets-list');
    const confirmApartarBtn = document.getElementById('confirm-apartar-btn');
    const maquinitaBtn = document.getElementById('maquinita-btn');
    
    // Modal elements
    const modal = document.getElementById('modal');
    if (modal) {
        const closeModalBtn = modal.querySelector('.close-btn');
        const whatsappForm = modal.querySelector('#whatsapp-form');
        const selectedCountSpan = modal.querySelector('#selected-count');

        let selectedTickets = [];

        // Lógica de selección de boletos
        if (ticketGrid) {
            ticketGrid.addEventListener('click', function(e) {
                if (e.target.classList.contains('ticket') && !e.target.classList.contains('apartado')) {
                    const ticketDiv = e.target;
                    const ticketNumber = ticketDiv.dataset.number;

                    ticketDiv.classList.toggle('selected');
                    if (ticketDiv.classList.contains('selected')) {
                        selectedTickets.push(ticketNumber);
                    } else {
                        selectedTickets = selectedTickets.filter(t => t !== ticketNumber);
                    }
                    updateApartarSeccion();
                }
            });
        }
        
        function updateApartarSeccion() {
            if (selectedTickets.length > 0) {
                apartarSeccion.style.display = 'block';
                selectedTicketsList.innerHTML = `<strong>${selectedTickets.join(', ')}</strong>`;
            } else {
                apartarSeccion.style.display = 'none';
            }
        }

        // Botón "Confirmar Apartado" -> Abre el modal
        if(confirmApartarBtn) {
            confirmApartarBtn.addEventListener('click', function() {
                if (selectedTickets.length > 0) {
                    selectedCountSpan.textContent = selectedTickets.length;
                    modal.style.display = 'flex';
                }
            });
        }

        // Cerrar el modal
        if(closeModalBtn) {
            closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
        }
        window.addEventListener('click', (e) => {
            if (e.target == modal) modal.style.display = 'none';
        });

        // Lógica del formulario para apartar
        if(whatsappForm) {
            whatsappForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const name = document.getElementById('name').value;
                const lastname = document.getElementById('lastname').value;
                const phone = document.getElementById('phone').value;
                const fullName = `${name} ${lastname}`;

                fetch('/apartar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: name,
                        lastname: lastname,
                        phone: phone,
                        tickets: selectedTickets
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const message = `¡Hola! 👋 Quiero confirmar mi apartado para la rifa.\n\n*Nombre:* ${fullName}\n*Teléfono:* ${phone}\n*Boletos:* ${selectedTickets.join(', ')}\n\n¡Gracias!`;
                        const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
                        window.location.href = whatsappUrl;
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Ocurrió un error al intentar apartar los boletos.');
                });
            });
        }

        // Maquinita de la Suerte
        if (maquinitaBtn) {
            maquinitaBtn.addEventListener('click', function() {
                const availableTickets = Array.from(document.querySelectorAll('.ticket:not(.apartado)'));
                if (availableTickets.length === 0) {
                    alert('¡No hay boletos disponibles!');
                    return;
                }
                
                selectedTickets.forEach(num => {
                    const el = document.querySelector(`.ticket[data-number="${num}"]`);
                    if(el) el.classList.remove('selected');
                });
                selectedTickets = [];

                for (let i = 0; i < 5 && availableTickets.length > 0; i++) {
                    const randomIndex = Math.floor(Math.random() * availableTickets.length);
                    const randomTicket = availableTickets.splice(randomIndex, 1)[0];
                    randomTicket.classList.add('selected');
                    selectedTickets.push(randomTicket.dataset.number);
                }
                updateApartarSeccion();
            });
        }
    }

    // Lógica del carrusel de imágenes
    const carousel = document.querySelector('.carousel');
    if (carousel) {
        const carouselInner = carousel.querySelector('.carousel-inner');
        const prevBtn = carousel.querySelector('.prev');
        const nextBtn = carousel.querySelector('.next');
        if(carouselInner && prevBtn && nextBtn) {
            let index = 0;
            const totalItems = carousel.querySelectorAll('.carousel-item').length;

            if (totalItems > 1) {
                nextBtn.addEventListener('click', () => {
                    index = (index + 1) % totalItems;
                    carouselInner.style.transform = `translateX(-${index * 100}%)`;
                });

                prevBtn.addEventListener('click', () => {
                    index = (index - 1 + totalItems) % totalItems;
                    carouselInner.style.transform = `translateX(-${index * 100}%)`;
                });
            } else {
                prevBtn.style.display = 'none';
                nextBtn.style.display = 'none';
            }
        }
    }
});
// --- Lógica para el menú hamburguesa ---
    const hamburgerBtn = document.querySelector('.hamburger-btn');
    const mainNav = document.getElementById('main-nav');

    if (hamburgerBtn && mainNav) {
        hamburgerBtn.addEventListener('click', function() {
            mainNav.classList.toggle('show');
        });
    }