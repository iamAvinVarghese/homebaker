
import os

template_content = """{% extends 'base.html' %}
{% load static %}
{% block title %}Advanced Analytics - Admin Panel{% endblock %}

{% block extra_css %}
<style>
    :root {
        --glass-bg: rgba(255, 255, 255, 0.95);
        --glass-border: rgba(255, 255, 255, 0.2);
        --primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        --success-gradient: linear-gradient(135deg, #10b981 0%, #059669 100%);
        --warning-gradient: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        --info-gradient: linear-gradient(135deg, #3b82f6 0%, #2dd4bf 100%);
        --ai-gradient: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%);
    }

    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
    }

    .ai-header {
        background: var(--ai-gradient);
        border-radius: 1.5rem;
        padding: 2rem;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .ai-header::after {
        content: '\\\\f0d0';
        font-family: 'Font Awesome 5 Free';
        font-weight: 900;
        position: absolute;
        right: -20px;
        bottom: -20px;
        font-size: 10rem;
        opacity: 0.1;
        transform: rotate(-15deg);
    }

    .insight-badge {
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
    }

    .table-glass {
        border-collapse: separate;
        border-spacing: 0 0.5rem;
    }

    .table-glass tr {
        background: white;
        border-radius: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }

    .table-glass td, .table-glass th {
        padding: 1.25rem 1rem;
        border: none;
    }

    .table-glass tr td:first-child { border-top-left-radius: 1rem; border-bottom-left-radius: 1rem; }
    .table-glass tr td:last-child { border-top-right-radius: 1rem; border-bottom-right-radius: 1rem; }

    .chart-container {
        position: relative;
        height: 300px;
        width: 100%;
    }
</style>
{% endblock %}

{% block content %}
<div class="row mb-5 align-items-center">
    <div class="col">
        <h1 class="display-5 fw-bold text-primary mb-1">Advanced Analytics</h1>
        <p class="text-muted mb-0">Harnessing AI to decode platform performance and growth.</p>
    </div>
    <div class="col-auto">
        <a href="{% url 'admin_dashboard' %}" class="btn btn-outline-primary border-0 rounded-pill px-4">
            <i class="fas fa-arrow-left me-2"></i> Dashboard
        </a>
    </div>
</div>

<!-- AI Intelligence Header -->
<div class="ai-header shadow-lg mb-5">
    <div class="row align-items-center">
        <div class="col-lg-8">
            <div class="d-flex align-items-center mb-3">
                <div class="bg-white bg-opacity-20 rounded-circle p-3 me-3">
                    <i class="fas fa-robot fa-2x"></i>
                </div>
                <h3 class="fw-bold mb-0 text-white">AI Business Intelligence</h3>
            </div>
            <p class="lead mb-0 opacity-90">{{ ai_summary }}</p>
        </div>
        <div class="col-lg-4 mt-4 mt-lg-0">
            <div class="bg-white bg-opacity-10 rounded-4 p-4">
                <h6 class="text-uppercase fw-bold small mb-3 opacity-75">Automated Insights</h6>
                <div class="d-flex flex-column gap-2">
                    {% for insight in ai_insights|slice:":3" %}
                    <div class="d-flex align-items-center">
                        <i class="fas {% if insight.priority == 'success' %}fa-check-circle text-success{% elif insight.priority == 'warning' %}fa-exclamation-triangle text-warning{% else %}fa-info-circle text-info{% endif %} me-2"></i>
                        <span class="small">{{ insight.message }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Revenue Projection Card -->
<div class="glass-card p-4 mb-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h5 class="fw-bold mb-0 text-primary"><i class="fas fa-chart-line me-2"></i>Revenue Intelligence & Projection</h5>
        <div class="text-end">
            <div class="small text-muted text-uppercase fw-bold">Next Month Forecast</div>
            <div class="h4 fw-bold text-primary mb-0">₹{{ revenue_data.predicted_value|floatformat:0 }}</div>
        </div>
    </div>
    <div class="chart-container">
        <canvas id="revenueAIChart"></canvas>
    </div>
</div>

<div class="row g-4 mb-5">
    <!-- Commission Breakdown -->
    <div class="col-12">
        <div class="glass-card p-4 overflow-hidden">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h5 class="fw-bold mb-0">Platform Commission Breakdown</h5>
                <span class="badge rounded-pill bg-success bg-opacity-10 text-success px-4 py-2 border border-success border-opacity-25">
                    Platform Total: ₹{{ total_platform_commission|floatformat:2 }}
                </span>
            </div>
            <div class="table-responsive">
                <table class="table table-glass align-middle mb-0">
                    <thead class="text-muted small text-uppercase fw-bold">
                        <tr>
                            <th class="ps-4">Baker Profile</th>
                            <th>Shop Name</th>
                            <th>Total Sales</th>
                            <th>Rate</th>
                            <th class="text-end pe-4">Commission</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in baker_commissions %}
                        <tr>
                            <td class="ps-4">
                                <div class="d-flex align-items-center">
                                    {% if item.baker.user_profile.profile_picture %}
                                    <img src="{{ item.baker.user_profile.profile_picture.url }}"
                                        class="rounded-circle me-3" width="40" height="40"
                                        style="object-fit: cover;">
                                    {% else %}
                                    <div class="rounded-circle bg-primary bg-opacity-10 text-primary d-flex align-items-center justify-content-center me-3"
                                        style="width: 40px; height: 40px;">
                                        <i class="fas fa-store small"></i>
                                    </div>
                                    {% endif %}
                                    <div>
                                        <div class="fw-bold text-dark small">{{ item.baker.user_profile.user.get_full_name|default:item.baker.user_profile.user.username }}</div>
                                        <div class="xsmall text-muted">{{ item.baker.user_profile.user.email }}</div>
                                    </div>
                                </div>
                            </td>
                            <td><span class="fw-medium">{{ item.baker.shop_name }}</span></td>
                            <td><span class="fw-bold">₹{{ item.revenue|floatformat:2 }}</span></td>
                            <td><span class="badge bg-info bg-opacity-10 text-info border border-info border-opacity-25">{{ item.commission_rate }}%</span></td>
                            <td class="text-end pe-4">
                                <span class="fw-bold text-success font-monospace">₹{{ item.commission_amount|floatformat:2 }}</span>
                            </td>
                        </tr>
                        {% empty %}
                        <tr>
                            <td colspan="5" class="text-center py-5 text-muted">
                                <i class="fas fa-receipt fa-3x mb-3 opacity-25"></i>
                                <p class="mb-0">No commission data available for the analysis period.</p>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<div class="row g-4 mb-5">
    <!-- Top Cakes -->
    <div class="col-md-6">
        <div class="glass-card p-4 h-100">
            <h5 class="fw-bold mb-4 text-primary">Top Selling Products</h5>
            <div class="list-group list-group-flush border-0 gap-2">
                {% for cake in top_cakes %}
                <div class="list-group-item d-flex align-items-center border-0 rounded-4 bg-light bg-opacity-25 px-3 py-3">
                    <div class="card-icon bg-white text-primary me-3 shadow-sm" style="width: 50px; height: 50px;">
                        <i class="fas fa-birthday-cake"></i>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-0 fw-bold">{{ cake.name }}</h6>
                        <small class="text-muted">{{ cake.baker.shop_name }}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge rounded-pill bg-primary px-3">{{ cake.sales_count }} Orders</span>
                    </div>
                </div>
                {% empty %}
                <div class="text-center py-5 text-muted">No data available</div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Top Bakers -->
    <div class="col-md-6">
        <div class="glass-card p-4 h-100">
            <h5 class="fw-bold mb-4 text-success">Elite Performers</h5>
            <div class="list-group list-group-flush border-0 gap-2">
                {% for baker in top_bakers %}
                <div class="list-group-item d-flex align-items-center border-0 rounded-4 bg-light bg-opacity-25 px-3 py-3">
                    {% if baker.user_profile.profile_picture %}
                    <img src="{{ baker.user_profile.profile_picture.url }}" class="rounded-circle me-3" width="50" height="50" style="object-fit: cover;">
                    {% else %}
                    <div class="rounded-circle bg-white text-success d-flex align-items-center justify-content-center me-3 shadow-sm" style="width: 50px; height: 50px;">
                        <i class="fas fa-award"></i>
                    </div>
                    {% endif %}
                    <div class="flex-grow-1">
                        <h6 class="mb-0 fw-bold">{{ baker.shop_name }}</h6>
                        <div class="text-warning small">
                            {% for i in "12345" %}
                            <i class="fas fa-star {% if forloop.counter <= baker.average_rating %}text-warning{% else %}text-muted opacity-25{% endif %} xsmall"></i>
                            {% endfor %}
                            <span class="text-muted ms-1">({{ baker.average_rating|floatformat:1 }})</span>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-success">₹{{ baker.total_revenue|floatformat:0 }}</div>
                        <small class="text-muted text-uppercase xsmall fw-bold">Revenue</small>
                    </div>
                </div>
                {% empty %}
                <div class="text-center py-5 text-muted">No data available</div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const ctx = document.getElementById('revenueAIChart').getContext('2d');
        
        // Data from view
        const labels = {{ revenue_data.labels|safe }};
        const data = {{ revenue_data.data|safe }};
        const predictedLabel = "{{ revenue_data.predicted_label }}";
        const predictedValue = {{ revenue_data.predicted_value }};
        
        // Add prediction point
        const allLabels = [...labels, predictedLabel];
        const allData = [...data, predictedValue];
        
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.2)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: allLabels,
                datasets: [{
                    label: 'Platform Revenue',
                    data: allData,
                    borderColor: '#6366f1',
                    borderWidth: 3,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#6366f1',
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    fill: true,
                    backgroundColor: gradient,
                    tension: 0.4,
                    segment: {
                        borderDash: ctx => ctx.p0DataIndex === labels.length - 1 ? [5, 5] : undefined,
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    }
                }
            }
        });
    });
</script>
{% endblock %}"""

with open('D:/HomeBakerProject/homebaker/templates/admin_analytics.html', 'w', encoding='utf-8') as f:
    f.write(template_content)

print("File updated successfully.")
