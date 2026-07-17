document.addEventListener("DOMContentLoaded", function () {
    const productGrid = document.getElementById("product-grid");
    const realProductsContainer = document.getElementById("real-products");

    if (!realProductsContainer) return;

    function createSkeleton() {
        return `
            <div class="product-card skeleton animate-pulse bg-surface-gray">
                <div class="bg-outline/10 aspect-[4/5] w-full"></div>
                <div class="py-4 px-4">
                    <div class="bg-outline/10 h-4 w-3/4 mb-2 rounded"></div>
                    <div class="bg-outline/10 h-3 w-1/3 rounded"></div>
                </div>
            </div>
        `;
    }

    function showSkeletons(count = 8) {
        productGrid.innerHTML = createSkeleton().repeat(count);
    }

    showSkeletons(8);

    setTimeout(() => {
        productGrid.innerHTML = "";
        
        productGrid.innerHTML = realProductsContainer.innerHTML;
        
        console.log("✅ Django template layout swapped successfully");
    }, 5000); 
});