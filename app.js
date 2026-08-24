const API_BASE = "http://127.0.0.1:8000/api";

document.addEventListener("DOMContentLoaded", () => {
    loadProducts();
    loadOrders();
});

function setPreset(promptText) {
    document.getElementById("promptInput").value = promptText;
}

async function runAgent(event) {
    event.preventDefault();
    const promptInput = document.getElementById("promptInput");
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const runBtn = document.getElementById("runBtn");
    const timelineContainer = document.getElementById("timelineContainer");
    const summaryCard = document.getElementById("summaryCard");

    // UI Loading state
    runBtn.disabled = true;
    runBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Running Agent...`;
    summaryCard.classList.add("d-none");

    timelineContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-grow text-primary mb-2"></div>
            <p class="text-muted small">PayAgent is evaluating catalog, calculating budget, and executing tool calls...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/agent/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();
        renderTimeline(data.decision_trail);
        renderSummary(data);

        // Refresh merchant dashboard in background
        loadProducts();
        loadOrders();
    } catch (error) {
        console.error("Agent execution error:", error);
        timelineContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i> Error connecting to PayAgent backend server: ${error.message}
            </div>
        `;
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = `<i class="bi bi-play-fill me-1"></i> Run Agent`;
    }
}

function renderTimeline(trail) {
    const timelineContainer = document.getElementById("timelineContainer");
    if (!trail || trail.length === 0) {
        timelineContainer.innerHTML = `<p class="text-muted">No decision trail recorded.</p>`;
        return;
    }

    let html = "";
    trail.forEach(step => {
        let iconClass = "bi-gear-fill";
        if (step.status === "SUCCESS") iconClass = "bi-check-lg";
        else if (step.status === "RECOVERING") iconClass = "bi-exclamation-triangle-fill";
        else if (step.status === "FAILED") iconClass = "bi-x-lg";

        const toolBadge = step.tool_name ? `<span class="step-tool ms-2"><i class="bi bi-wrench me-1"></i>${step.tool_name}</span>` : "";

        html += `
            <div class="timeline-step">
                <div class="step-icon ${step.status}">
                    <i class="bi ${iconClass}"></i>
                </div>
                <div class="step-content">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <div>
                            <span class="step-title">${step.step}</span>
                            ${toolBadge}
                        </div>
                        <span class="text-muted small" style="font-size:0.75rem;">${step.timestamp}</span>
                    </div>
                    <p class="mb-1 text-light small">${step.reasoning}</p>
                    ${step.output ? `<pre class="bg-dark p-2 rounded text-info small mb-0 mt-2" style="font-size:0.75rem; max-height:120px; overflow:auto;">${JSON.stringify(step.output, null, 2)}</pre>` : ''}
                </div>
            </div>
        `;
    });

    timelineContainer.innerHTML = html;
}

function renderSummary(data) {
    const summaryCard = document.getElementById("summaryCard");
    const summaryStatusBadge = document.getElementById("summaryStatusBadge");
    const sumItemName = document.getElementById("sumItemName");
    const sumAmount = document.getElementById("sumAmount");
    const sumOrderId = document.getElementById("sumOrderId");
    const sumPaymentLink = document.getElementById("sumPaymentLink");
    const sumPaymentId = document.getElementById("sumPaymentId");

    summaryCard.classList.remove("d-none");

    if (data.final_status === "COMPLETED") {
        summaryStatusBadge.className = "badge bg-success";
        summaryStatusBadge.innerText = "TRANSACTION COMPLETED";
        sumItemName.innerText = data.purchased_item ? data.purchased_item.name : "N/A";
        sumAmount.innerText = data.total_amount_spent.toLocaleString();
        sumOrderId.innerText = data.order_id || "N/A";
        sumPaymentLink.innerText = data.payment_link || "N/A";
        sumPaymentLink.href = data.payment_link || "#";
        sumPaymentId.innerText = data.payment_id || "N/A";
    } else {
        summaryStatusBadge.className = "badge bg-danger";
        summaryStatusBadge.innerText = "FAILED";
        sumItemName.innerText = "None";
        sumAmount.innerText = "0";
        sumOrderId.innerText = "N/A";
        sumPaymentLink.innerText = "N/A";
        sumPaymentId.innerText = "N/A";
    }
}

function clearLogs() {
    document.getElementById("timelineContainer").innerHTML = `
        <div class="empty-state text-center py-5 text-muted">
            <i class="bi bi-play-circle fs-1 opacity-50 mb-3 d-block"></i>
            <p class="mb-0">Click "Run Agent" or pick a preset prompt to watch PayAgent discover, decide, and pay in real time!</p>
        </div>
    `;
    document.getElementById("summaryCard").classList.add("d-none");
}

async function loadProducts() {
    try {
        const res = await fetch(`${API_BASE}/products`);
        const products = await res.json();
        renderCatalog(products);
    } catch (e) {
        console.error("Failed loading products:", e);
    }
}

function renderCatalog(products) {
    const catalogGrid = document.getElementById("catalogGrid");
    let html = "";
    products.forEach(p => {
        const stockBadge = p.stock > 0 
            ? `<span class="badge bg-success-subtle text-success">In Stock (${p.stock})</span>` 
            : `<span class="badge bg-danger-subtle text-danger">OUT OF STOCK (0)</span>`;

        html += `
            <div class="col-md-6 col-lg-4">
                <div class="card product-card h-100">
                    <img src="${p.image_url}" class="product-img" alt="${p.name}">
                    <div class="card-body d-flex flex-column justify-content-between p-3">
                        <div>
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <span class="badge bg-secondary small">${p.category}</span>
                                ${stockBadge}
                            </div>
                            <h6 class="fw-bold text-white mb-1">${p.name}</h6>
                            <p class="text-muted small mb-2" style="font-size:0.8rem; line-height:1.3;">${p.description}</p>
                        </div>
                        <div>
                            <div class="d-flex justify-content-between align-items-center mt-2">
                                <span class="fw-bold text-info fs-5">₹${p.price.toLocaleString()}</span>
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline-warning" onclick="toggleStock('${p.id}', ${p.stock > 0 ? 0 : 10})">
                                        ${p.stock > 0 ? 'Set Stock=0' : 'Restock 10'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    catalogGrid.innerHTML = html;
}

async function toggleStock(productId, newStock) {
    try {
        await fetch(`${API_BASE}/products/${productId}/stock?stock=${newStock}`, { method: "PUT" });
        loadProducts();
    } catch (e) {
        console.error("Failed toggling stock:", e);
    }
}

async function loadOrders() {
    try {
        const res = await fetch(`${API_BASE}/orders`);
        const orders = await res.json();
        renderOrders(orders);
    } catch (e) {
        console.error("Failed loading orders:", e);
    }
}

function renderOrders(orders) {
    const ordersList = document.getElementById("ordersList");
    if (!orders || orders.length === 0) {
        ordersList.innerHTML = `<p class="text-muted small">No agent orders recorded yet.</p>`;
        return;
    }
    let html = "";
    orders.forEach(o => {
        html += `
            <div class="order-item">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <code class="text-info">${o.id}</code>
                    <span class="badge bg-success-subtle text-success">${o.status}</span>
                </div>
                <div class="fw-bold text-white small">${o.product_name}</div>
                <div class="d-flex justify-content-between text-muted small mt-1">
                    <span>Receipt: ${o.receipt}</span>
                    <span class="text-warning fw-semibold">₹${(o.amount / 100).toLocaleString()}</span>
                </div>
            </div>
        `;
    });
    ordersList.innerHTML = html;
}
