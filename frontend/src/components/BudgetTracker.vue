<template>
  <div class="budget-tracker">
    <div class="card">
      <div class="budget-header">
        <h2 class="card-title">Budget Management</h2>
        <button 
          @click="showAddBudget = !showAddBudget" 
          class="add-budget-button"
        >
          {{ showAddBudget ? 'Cancel' : 'Add Budget' }}
        </button>
      </div>
      
      <!-- Add Budget Form -->
      <div v-if="showAddBudget" class="add-budget-form">
        <div class="form-group">
          <label class="form-label" for="category">Category</label>
          <select 
            v-model="newBudget.category" 
            id="category"
            class="form-input"
          >
            <option value="">Select a category</option>
            <option v-for="category in availableCategories" :key="category" :value="category">
              {{ category }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="amount">Monthly Budget Amount</label>
          <div class="amount-input-container">
            <span class="currency-symbol">$</span>
            <input 
              v-model="newBudget.amount" 
              id="amount"
              class="form-input amount-input" 
              type="number" 
              step="0.01" 
              placeholder="0.00"
            />
          </div>
        </div>
        
        <button 
          @click="addBudget" 
          class="submit-button"
          :disabled="!isValidBudget || isSubmitting"
        >
          {{ isSubmitting ? 'Saving...' : 'Save Budget' }}
        </button>
      </div>
      
      <!-- Loading state -->
      <div v-if="isLoading" class="loading-container">
        <div class="spinner"></div>
        <p class="loading-text">Loading budgets...</p>
      </div>
      
      <!-- Budgets List -->
      <div v-else-if="budgets.length === 0 && !showAddBudget" class="empty-state">
        <svg class="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <p class="empty-text">No budgets set. Add a budget to track your spending.</p>
      </div>
      
      <div v-else-if="!showAddBudget" class="budget-list-container">
        <div v-for="budget in budgets" :key="budget.id" class="budget-item">
          <div class="budget-details">
            <div class="budget-category">
              <span class="category-badge" :class="'category-' + budget.category.toLowerCase().replace(' ', '-')">
                {{ budget.category }}
              </span>
            </div>
            <div class="budget-amount">${{ budget.amount.toFixed(2) }}/month</div>
          </div>
          
          <div class="budget-progress">
            <div class="progress-info">
              <span class="spent-amount">${{ getBudgetStatus(budget.category).spent.toFixed(2) }} spent</span>
              <span class="remaining-amount">${{ getBudgetStatus(budget.category).remaining.toFixed(2) }} remaining</span>
            </div>
            <div class="progress-bar-container">
              <div 
                class="progress-bar" 
                :style="{ width: getBudgetStatus(budget.category).percentageWidth, 
                         backgroundColor: getBudgetStatus(budget.category).color }"
              ></div>
            </div>
            <div class="progress-percentage">
              {{ Math.round(getBudgetStatus(budget.category).percentage) }}% used
            </div>
          </div>
          
          <div class="budget-actions">
            <button @click="deleteBudget(budget.id)" class="delete-button">
              <svg class="delete-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

// Configure the base URL for your API
const API_URL = 'http://localhost:8000';

export default {
  name: 'BudgetTracker',
  props: {
    expenses: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      budgets: [],
      budgetStatus: [],
      showAddBudget: false,
      newBudget: {
        category: '',
        amount: ''
      },
      isLoading: false,
      isSubmitting: false,
      error: null
    }
  },
  computed: {
    isValidBudget() {
      return this.newBudget.category && 
             this.newBudget.amount && 
             parseFloat(this.newBudget.amount) > 0;
    },
    // Get unique categories from expenses
    availableCategories() {
      const categories = new Set(this.expenses.map(expense => expense.category));
      return Array.from(categories).sort();
    }
  },
  mounted() {
    this.fetchBudgets();
    this.fetchBudgetStatus();
  },
  watch: {
    // Watch expenses for changes to update budget status
    expenses: {
      handler() {
        this.fetchBudgetStatus();
      },
      deep: true
    }
  },
  methods: {
    async fetchBudgets() {
      this.isLoading = true;
      try {
        const response = await axios.get(`${API_URL}/budgets/`);
        this.budgets = response.data;
      } catch (error) {
        console.error('Error fetching budgets:', error);
        this.error = 'Failed to load budgets. Please try again.';
      } finally {
        this.isLoading = false;
      }
    },
    async fetchBudgetStatus() {
      try {
        const response = await axios.get(`${API_URL}/budget_status/`);
        this.budgetStatus = response.data;
      } catch (error) {
        console.error('Error fetching budget status:', error);
      }
    },
    async addBudget() {
      if (!this.isValidBudget) return;
      
      this.isSubmitting = true;
      try {
        const response = await axios.post(`${API_URL}/budgets/`, {
          category: this.newBudget.category,
          amount: parseFloat(this.newBudget.amount),
          period: 'monthly'
        });
        
        // Add new budget to the list or update existing
        const index = this.budgets.findIndex(b => b.id === response.data.id);
        if (index !== -1) {
          this.budgets.splice(index, 1, response.data);
        } else {
          this.budgets.push(response.data);
        }
        
        // Reset form
        this.newBudget = {
          category: '',
          amount: ''
        };
        
        // Close add budget form
        this.showAddBudget = false;
        
        // Refresh budget status
        this.fetchBudgetStatus();
        
      } catch (error) {
        console.error('Error adding budget:', error);
        alert('Failed to add budget. Please try again.');
      } finally {
        this.isSubmitting = false;
      }
    },
    async deleteBudget(id) {
      if (!confirm('Are you sure you want to delete this budget?')) {
        return;
      }
      
      try {
        await axios.delete(`${API_URL}/budgets/${id}`);
        
        // Remove budget from list
        this.budgets = this.budgets.filter(budget => budget.id !== id);
        
        // Refresh budget status
        this.fetchBudgetStatus();
        
      } catch (error) {
        console.error('Error deleting budget:', error);
        alert('Failed to delete budget. Please try again.');
      }
    },
    getBudgetStatus(category) {
      // Find budget status for this category
      const status = this.budgetStatus.find(s => s.category === category);
      
      if (!status) {
        // Calculate status based on expenses if not found in API response
        const categoryExpenses = this.expenses.filter(e => e.category === category);
        const spent = categoryExpenses.reduce((sum, expense) => sum + expense.amount, 0);
        const budget = this.budgets.find(b => b.category === category);
        const budgetAmount = budget ? budget.amount : 0;
        const remaining = budgetAmount - spent;
        const percentage = budgetAmount > 0 ? (spent / budgetAmount) * 100 : 0;
        
        return {
          spent,
          remaining: Math.max(0, remaining),
          percentage,
          percentageWidth: `${Math.min(100, percentage)}%`,
          color: percentage > 90 ? '#ef4444' : percentage > 75 ? '#f59e0b' : '#10b981'
        };
      }
      
      return {
        spent: status.spent,
        remaining: Math.max(0, status.remaining),
        percentage: status.percentage_used,
        percentageWidth: `${Math.min(100, status.percentage_used)}%`,
        color: status.percentage_used > 90 ? '#ef4444' : status.percentage_used > 75 ? '#f59e0b' : '#10b981'
      };
    }
  }
}
</script>

<style scoped>
.budget-tracker {
  margin-bottom: 2rem;
}

.budget-tracker .card {
  margin-bottom: 3rem; /* Extra margin at bottom */
  border: 2px solid #e5e7eb; /* Make border more visible */
  background-color: #ffffff; /* Ensure white background */
  position: relative;     /* For proper positioning */
  z-index: 5;            /* Ensure card is above footer */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15); /* Stronger shadow */
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.budget-tracker .card-title {
  font-size: 1.6rem; /* Larger title */
  color: #1e40af; /* Blue title color */
  margin-bottom: 2rem; /* More space below title */
}

.add-budget-button {
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-budget-button:hover {
  background-color: #2563eb;
  transform: translateY(-1px);
}

.add-budget-form {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e5e7eb;
}

.budget-list-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.budget-item {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  transition: transform 0.2s, box-shadow 0.2s;
}

.budget-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.budget-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.budget-amount {
  font-weight: 600;
  color: #1f2937;
}

.budget-progress {
  margin-bottom: 0.75rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.spent-amount {
  color: #4b5563;
}

.remaining-amount {
  color: #1f2937;
  font-weight: 500;
}

.progress-bar-container {
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.progress-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s, background-color 0.3s;
}

.progress-percentage {
  text-align: right;
  font-size: 0.75rem;
  color: #6b7280;
}

.budget-actions {
  display: flex;
  justify-content: flex-end;
}

.delete-button {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.delete-button:hover {
  background-color: #fee2e2;
  color: #b91c1c;
}

.delete-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  margin: 1rem 0;
  color: #6b7280;
}

.empty-icon {
  width: 3rem;
  height: 3rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.empty-text {
  text-align: center;
  font-size: 0.875rem;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.75rem;
}

.loading-text {
  color: #6b7280;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>