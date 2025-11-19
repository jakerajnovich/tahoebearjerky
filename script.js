// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State
let products = []; // Will be loaded from API
let cart = [];
let currentCategory = 'all';

// DOM Elements
const productsGrid = document.getElementById('productsGrid');
const filterTabs = document.querySelectorAll('.filter-tab');
const cartBtn = document.getElementById('cartBtn');
const cartModal = document.getElementById('cartModal');
const cartClose = document.getElementById('cartClose');
const cartOverlay = document.getElementById('cartOverlay');
const cartItemsContainer = document.getElementById('cartItems');
const cartCount = document.getElementById('cartCount');
const cartTotal = document.getElementById('cartTotal');
const navbar = document.getElementById('navbar');

// API Functions
async function fetchProducts(category = 'all') {
    try {
        const url = category === 'all'
            ? `${API_BASE_URL}/products`
            : `${API_BASE_URL}/products?category=${category}`;

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Failed to fetch products');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching products:', error);
        // Return empty array if API fails
        return [];
    }
}

async function loadProducts() {
    try {
        products = await fetchProducts(currentCategory);
        renderProducts();
    } catch (error) {
        console.error('Error loading products:', error);
        productsGrid.innerHTML = '<p style="text-align: center; color: #888; grid-column: 1/-1;">Unable to load products. Please try again later.</p>';
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    setupEventListeners();
    updateCartUI();
});

// Event Listeners
function setupEventListeners() {
    // Filter Tabs
    filterTabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            // Update active tab
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update category and reload products
            currentCategory = tab.dataset.category;
            await loadProducts();
        });
    });

    // Cart Modal
    cartBtn.addEventListener('click', openCart);
    cartClose.addEventListener('click', closeCart);
    cartOverlay.addEventListener('click', closeCart);

    // Navbar Scroll Effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            navbar.style.padding = '0.5rem 0';
        } else {
            navbar.style.boxShadow = 'none';
            navbar.style.padding = '1rem 0';
        }
    });

    // Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Render Products
function renderProducts() {
    productsGrid.innerHTML = '';

    if (products.length === 0) {
        productsGrid.innerHTML = '<p style="text-align: center; color: #888; grid-column: 1/-1;">No products available.</p>';
        return;
    }

    products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card';

        // Use emoji if no image_url, otherwise use image
        const productImage = product.image_url
            ? `<img src="${product.image_url}" alt="${product.name}">`
            : product.emoji || '📦';

        productCard.innerHTML = `
            <div class="product-image">
                ${productImage}
                <div class="product-overlay">
                    <button class="quick-view-btn" onclick="addToCart(${product.id})">Quick Add</button>
                </div>
            </div>
            <div class="product-info">
                <div class="product-category">${product.category_slug || product.category_name}</div>
                <h3 class="product-title">${product.name}</h3>
                <p class="product-description" style="font-size: 0.9rem; color: #666; margin-bottom: 1rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${product.description}</p>
                <div class="product-footer">
                    <span class="product-price">$${product.price}</span>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">Add to Cart</button>
                </div>
            </div>
        `;
        productsGrid.appendChild(productCard);
    });
}

// Cart Functions
function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    const existingItem = cart.find(item => item.id === productId);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            ...product,
            quantity: 1
        });
    }

    updateCartUI();
    openCart();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    updateCartUI();
}

function updateCartUI() {
    // Update Count
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    cartCount.textContent = totalItems;

    // Update Total
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartTotal.textContent = `$${total.toFixed(2)}`;

    // Render Items
    cartItemsContainer.innerHTML = '';

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p style="text-align: center; color: #888; margin-top: 2rem;">Your cart is empty.</p>';
        return;
    }

    cart.forEach(item => {
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';

        // Use emoji or image for cart display
        const itemImage = item.image_url
            ? `<img src="${item.image_url}" alt="${item.name}" style="width: 100%; height: 100%; object-fit: cover;">`
            : item.emoji || '📦';

        cartItem.innerHTML = `
            <div class="cart-item-image">${itemImage}</div>
            <div class="cart-item-details">
                <div class="cart-item-title">${item.name}</div>
                <div class="cart-item-price">$${item.price} x ${item.quantity}</div>
                <div class="cart-item-remove" onclick="removeFromCart(${item.id})">Remove</div>
            </div>
        `;
        cartItemsContainer.appendChild(cartItem);
    });
}

function openCart() {
    cartModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeCart() {
    cartModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Expose functions to global scope for HTML onclick attributes
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
