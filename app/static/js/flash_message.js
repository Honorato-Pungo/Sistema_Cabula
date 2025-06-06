window.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert-dismissible');

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            alert.classList.add('fade');

            setTimeout(() => {
                alert.remove();
            }, 300); // tempo para o fade completar
        }, 5000); // tempo visível: 5 segundos
    });
});

