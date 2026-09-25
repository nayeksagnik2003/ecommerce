// Lightweight demo cart, persisted client-side only (localStorage).
// There is no real checkout/order backend here — this is just enough
// to make "add to cart" feel real for a front-end demo.
(function () {
  const KEY = 'circuitloop_cart';

  function readCart() {
    try {
      return JSON.parse(localStorage.getItem(KEY)) || [];
    } catch (e) {
      return [];
    }
  }

  function writeCart(items) {
    try {
      localStorage.setItem(KEY, JSON.stringify(items));
    } catch (e) { /* storage unavailable, fail silently */ }
    updateBadge();
  }

  function updateBadge() {
    const badge = document.getElementById('cart-badge');
    if (badge) badge.textContent = readCart().length;
  }

  window.addToCart = function (productId, name, price) {
    const items = readCart();
    items.push({ productId, name, price, addedAt: Date.now() });
    writeCart(items);

    const link = document.getElementById('cart-link');
    if (link) {
      const original = link.textContent;
      link.insertAdjacentHTML('beforeend', '');
      const toast = document.createElement('span');
      toast.textContent = ' ✓ added';
      toast.style.color = '#FFC93C';
      toast.style.marginLeft = '6px';
      toast.style.fontSize = '0.75rem';
      link.appendChild(toast);
      setTimeout(() => toast.remove(), 1200);
    }
  };

  document.addEventListener('DOMContentLoaded', updateBadge);
})();
