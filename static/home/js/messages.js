/* ============================================
   Generic message helpers
   ============================================ */
// Auto-dismiss alert messages after 5 seconds without relying on jQuery
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (el) {
            // Use Bootstrap's Alert API if available
            try {
                var alert = bootstrap.Alert.getOrCreateInstance(el);
                alert.close();
            } catch (e) {
                // Fallback: simply hide the element
                el.style.display = 'none';
            }
        });
    }, 5000);
});
