document.addEventListener('DOMContentLoaded', () => {
    const claims = JSON.parse(localStorage.getItem('bookClaims')) || [];
    const claimForm = document.getElementById('claimForm');
    const claimedBooks = document.getElementById('claimedBooks');

    if (claimForm) {
        claimForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const course = document.getElementById('course').value.trim();
            const bookTitle = document.getElementById('bookTitle').value.trim();
            const quantity = document.getElementById('quantity').value;
            const phone = document.getElementById('phone').value.trim();

            const claim = {
                course,
                bookTitle,
                quantity,
                phone,
                timestamp: new Date().toLocaleString()
            };

            claims.push(claim);
            localStorage.setItem('bookClaims', JSON.stringify(claims));

            alert('Book claim submitted successfully!');
            claimForm.reset();
        });
    }

    if (claimedBooks) {
        claimedBooks.innerHTML = '';

        if (claims.length === 0) {
            claimedBooks.innerHTML = '<li>No books claimed yet.</li>';
            return;
        }

        claims.forEach(claim => {
            const li = document.createElement('li');
            li.textContent = `${claim.bookTitle} (${claim.quantity}) - Course: ${claim.course}${claim.phone ? ' - Phone: ' + claim.phone : ''} - Claimed on: ${claim.timestamp}`;
            claimedBooks.appendChild(li);
        });
    }
});
