
import os

template_content = """{% extends 'base.html' %}
{% load static %}
{% block title %}Admin Dashboard{% endblock %}

{% block content %}
<style>
    :root {
        --glass-bg: rgba(255, 255, 255, 0.95);
        --glass-border: rgba(255, 255, 255, 0.2);
        --primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        --success-gradient: linear-gradient(135deg, #10b981 0%, #059669 100%);
        --warning-gradient: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        --info-gradient: linear-gradient(135deg, #3b82f6 0%, #2dd4bf 100%);
    }

    body[data-theme="dark"] {
        background-color: #0d1117;
        color: #c9d1d9;
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

    .stat-card {
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        z-index: 1;
    }

    .card-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
    }
</style>

<div class="container-fluid py-4">
    <div class="d-flex align-items-center mb-5">
        {% if user.profile.profile_picture %}
        <img src="{{ user.profile.profile_picture.url }}" alt="Profile"
            class="rounded-circle me-3 shadow-sm border border-2 border-white"
            style="width: 72px; height: 72px; object-fit: cover;">
        {% endif %}
        <div>
            <h1 class="display-5 fw-bold mb-0 text-primary">Admin Dashboard</h1>
            <p class="text-muted mb-0">Platform overview and business intelligence</p>
        </div>
    </div>

    <!-- KPI Cards -->
    <div class="row g-4 mb-5">
        <div class="col-md-3">
            <a href="{% url 'admin_users' %}" class="text-decoration-none">
                <div class="glass-card stat-card text-primary h-100">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <p class="text-muted small fw-bold text-uppercase mb-1">Total Users</p>
                            <h2 class="display-6 fw-bold mb-0 text-dark">{{ total_users }}</h2>
                        </div>
                        <div class="card-icon bg-primary bg-opacity-10 text-primary">
                            <i class="fas fa-users"></i>
                        </div>
                    </div>
                    <div class="small text-muted">
                        <span class="fw-bold">{{ total_customers }}</span> Customers | <span class="fw-bold">{{ total_bakers }}</span> Bakers
                    </div>
                </div>
            </a>
        </div>
        <div class="col-md-3">
            <a href="{% url 'admin_commission' %}" class="text-decoration-none">
                <div class="glass-card stat-card text-success h-100">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <p class="text-muted small fw-bold text-uppercase mb-1">Total Revenue</p>
                            <h2 class="display-6 fw-bold mb-0 text-dark">₹{{ total_revenue|floatformat:0 }}</h2>
                        </div>
                        <div class="card-icon bg-success bg-opacity-10 text-success">
                            <i class="fas fa-wallet"></i>
                        </div>
                    </div>
                    <div class="small text-muted">
                        Monthly: <span class="fw-bold">₹{{ monthly_revenue|floatformat:0 }}</span>
                    </div>
                </div>
            </a>
        </div>
        <div class="col-md-3">
            <a href="{% url 'admin_orders_list' %}" class="text-decoration-none">
                <div class="glass-card stat-card text-info h-100">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <p class="text-muted small fw-bold text-uppercase mb-1">Total Orders</p>
                            <h2 class="display-6 fw-bold mb-0 text-dark">{{ total_orders }}</h2>
                        </div>
                        <div class="card-icon bg-info bg-opacity-10 text-info">
                            <i class="fas fa-shopping-bag"></i>
                        </div>
                    </div>
                    <div class="small text-muted">
                        Completed: <span class="fw-bold">{{ completed_orders_count }}</span> | Pending: <span class="fw-bold">{{ pending_orders_count }}</span>
                    </div>
                </div>
            </a>
        </div>
        <div class="col-md-3">
            <a href="{% url 'admin_commission' %}" class="text-decoration-none">
                <div class="glass-card stat-card text-warning h-100">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <p class="text-muted small fw-bold text-uppercase mb-1">Platform Commission</p>
                            <h2 class="display-6 fw-bold mb-0 text-dark">₹{{ total_commission|floatformat:0 }}</h2>
                        </div>
                        <div class="card-icon bg-warning bg-opacity-10 text-warning">
                            <i class="fas fa-chart-pie"></i>
                        </div>
                    </div>
                    <div class="small text-muted">
                        Bakers Pending: <span class="fw-bold">{{ pending_bakers }}</span>
                    </div>
                </div>
            </a>
        </div>
    </div>

    <!-- Charts Row -->
    <div class="row g-4 mb-5">
        <div class="col-md-6">
            <div class="glass-card stat-card h-100">
                <h5 class="fw-bold mb-4 text-primary"><i class="fas fa-chart-line me-2"></i>Monthly Revenue</h5>
                <div style="height: 300px;">
                    <canvas id="revenueChart"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="glass-card stat-card h-100">
                <h5 class="fw-bold mb-4 text-info"><i class="fas fa-chart-bar me-2"></i>User Growth</h5>
                <div style="height: 300px;">
                    <canvas id="userGrowthChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Recent Activity -->
    <div class="row g-4 mb-5">
        <div class="col-md-6">
            <div class="glass-card p-0 overflow-hidden h-100">
                <div class="card-header bg-transparent border-0 px-4 py-3 d-flex justify-content-between align-items-center border-bottom">
                    <h5 class="fw-bold mb-0"><i class="fas fa-history me-2 text-primary"></i>Recent Orders</h5>
                    <a href="{% url 'admin_orders_list' %}" class="btn btn-sm btn-outline-primary rounded-pill px-3">View All</a>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-borderless align-middle mb-0">
                            <thead class="bg-light bg-opacity-50">
                                <tr class="text-muted small text-uppercase fw-bold">
                                    <th class="ps-4">ID</th>
                                    <th>Customer</th>
                                    <th>Amount</th>
                                    <th class="pe-4">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for order in recent_orders %}
                                <tr class="border-bottom">
                                    <td class="ps-4 fw-bold">#{{ order.clean_id }}</td>
                                    <td>
                                        <div class="fw-bold">{{ order.customer.get_full_name|default:"-" }}</div>
                                        <div class="xsmall text-muted">{{ order.customer.username }}</div>
                                    </td>
                                    <td>₹{{ order.total_amount }}</td>
                                    <td class="pe-4">
                                        <span class="badge rounded-pill bg-primary bg-opacity-10 text-primary px-3 py-2">
                                            {{ order.get_status_display }}
                                        </span>
                                    </td>
                                </tr>
                                {% empty %}
                                <tr>
                                    <td colspan="4" class="text-center py-5 text-muted">No recent orders</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="glass-card p-0 overflow-hidden h-100">
                <div class="card-header bg-transparent border-0 px-4 py-3 d-flex justify-content-between align-items-center border-bottom">
                    <h5 class="fw-bold mb-0"><i class="fas fa-list-ul me-2 text-info"></i>System Audit</h5>
                    <a href="{% url 'admin_audit_logs' %}" class="btn btn-sm btn-outline-info rounded-pill px-3">Details</a>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-borderless align-middle mb-0">
                            <thead class="bg-light bg-opacity-50">
                                <tr class="text-muted small text-uppercase fw-bold">
                                    <th class="ps-4">User</th>
                                    <th>Action</th>
                                    <th class="pe-4">Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for log in recent_audit_logs %}
                                <tr class="border-bottom">
                                    <td class="ps-4">
                                        <div class="fw-bold">{{ log.user.get_full_name|default:"-" }}</div>
                                        <div class="xsmall text-muted">{{ log.user.username|default:"System" }}</div>
                                    </td>
                                    <td>
                                        <span class="small">{{ log.get_action_display }}</span>
                                    </td>
                                    <td class="pe-4">
                                        <span class="small text-muted">{{ log.created_at|timesince }} ago</span>
                                    </td>
                                </tr>
                                {% empty %}
                                <tr>
                                    <td colspan="3" class="text-center py-5 text-muted">No audit logs</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="glass-card p-4">
        <h5 class="fw-bold mb-4 text-primary"><i class="fas fa-bolt me-2"></i>Quick Management</h5>
        <div class="d-flex flex-wrap gap-3">
            <a href="{% url 'admin_bakers' %}" class="btn btn-primary rounded-pill px-4 py-2 shadow-sm">
                <i class="fas fa-store me-2"></i>Manage Bakers
            </a>
            <a href="{% url 'admin_users' %}" class="btn btn-outline-secondary rounded-pill px-4 py-2">
                <i class="fas fa-users me-2"></i>Manage Users
            </a>
            <a href="{% url 'admin_audit_logs' %}" class="btn btn-outline-info rounded-pill px-4 py-2">
                <i class="fas fa-scroll me-2"></i>Audit Logs
            </a>
            <a href="{% url 'admin_commission' %}" class="btn btn-outline-success rounded-pill px-4 py-2">
                <i class="fas fa-percentage me-2"></i>Commissions
            </a>
            <a href="{% url 'admin_analytics' %}" class="btn btn-outline-warning rounded-pill px-4 py-2">
                <i class="fas fa-microchip me-2"></i>AI Analytics
            </a>
        </div>
    </div>
</div>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{{ chart_data | json_script:"adminChartData" }}
<script>
    // Revenue Chart
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');
    const chartData = JSON.parse(document.getElementById('adminChartData').textContent);
    const revenueData = chartData.monthly_revenue;
    new Chart(revenueCtx, {
        type: 'line',
        data: {
            labels: revenueData.map(d => d.month),
            datasets: [{
                label: 'Revenue (₹)',
                data: revenueData.map(d => d.revenue),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // User Growth Chart
    const userCtx = document.getElementById('userGrowthChart').getContext('2d');
    const userData = chartData.user_growth;
    new Chart(userCtx, {
        type: 'bar',
        data: {
            labels: userData.map(d => d.month),
            datasets: [{
                label: 'New Users',
                data: userData.map(d => d.users),
                backgroundColor: 'rgba(54, 162, 235, 0.6)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
</script>
{% endblock %}"""

with open('D:/HomeBakerProject/homebaker/templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(template_content)

print("File updated successfully.")
