<template>
  <div class="csv-import-section">
    <div class="card">
      <h2 class="card-title">Import Expenses</h2>
      
      <!-- Upload form -->
      <div v-if="!isProcessing && !isSuccess" class="upload-form">
        <p class="import-description">
          Import expenses from your bank statement CSV file.
        </p>
        
        <div class="upload-container" 
             :class="{ 'drag-over': isDragging }"
             @dragover.prevent="isDragging = true"
             @dragleave.prevent="isDragging = false"
             @drop.prevent="handleDrop">
          <svg class="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p class="upload-text">
            <span class="upload-prompt">Drag and drop your CSV file here, or</span>
            <label class="file-select-button">
              Browse Files
              <input 
                type="file" 
                accept=".csv" 
                class="hidden-file-input" 
                @change="handleFileSelect"
              />
            </label>
          </p>
          <p class="file-format-note">
            Supported format: CSV files from most major banks
          </p>
        </div>
        
        <div v-if="selectedFile" class="selected-file">
          <div class="file-info">
            <svg class="file-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span class="file-name">{{ selectedFile.name }}</span>
            <button class="remove-file-button" @click="removeFile">✕</button>
          </div>
          
          <!-- File mapping options -->
          <div class="mapping-options" v-if="csvHeaders.length > 0">
            <h3 class="mapping-title">Column Mapping</h3>
            <p class="mapping-description">
              Please match your CSV columns to our expense fields:
            </p>
            
            <div class="mapping-form">
              <div class="mapping-group">
                <label class="mapping-label">Description Column:</label>
                <select v-model="columnMapping.description" class="mapping-select">
                  <option value="">Select column</option>
                  <option v-for="header in csvHeaders" :key="header" :value="header">
                    {{ header }}
                  </option>
                </select>
              </div>
              
              <div class="mapping-group">
                <label class="mapping-label">Amount Column:</label>
                <select v-model="columnMapping.amount" class="mapping-select">
                  <option value="">Select column</option>
                  <option v-for="header in csvHeaders" :key="header" :value="header">
                    {{ header }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          
          <button @click="importExpenses" class="import-button" :disabled="isImportButtonDisabled">
            Import Expenses
          </button>
        </div>
      </div>
      
      <!-- Processing state -->
      <div v-if="isProcessing" class="processing-state">
        <div class="spinner"></div>
        <p class="processing-text">Processing your file...</p>
      </div>
      
      <!-- Success state -->
      <div v-if="isSuccess" class="success-state">
        <div class="success-icon-container">
          <svg class="success-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 class="success-title">Import Successful!</h3>
        <p class="success-message">
          Successfully imported {{ importedCount }} expenses from your CSV file.
        </p>
        <div class="import-summary">
          <div class="summary-item">
            <span class="summary-label">Total Amount:</span>
            <span class="summary-value">${{ importTotal.toFixed(2) }}</span>
          </div>
        </div>
        <button @click="resetImport" class="done-button">Done</button>
      </div>
      
      <!-- Error state -->
      <div v-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button @click="resetImport" class="retry-button">Try Again</button>
      </div>
    </div>
  </div>
</template>

<script>
import Papa from 'papaparse';
import axios from 'axios';

// Configure the base URL for your API
const API_URL = 'http://localhost:8000';

export default {
  name: 'CsvImport',
  data() {
    return {
      isDragging: false,
      selectedFile: null,
      csvData: null,
      csvHeaders: [],
      columnMapping: {
        description: '',
        amount: ''
      },
      isProcessing: false,
      isSuccess: false,
      importedCount: 0,
      importTotal: 0,
      error: null
    };
  },
  computed: {
    isImportButtonDisabled() {
      // Disable import button if any mapping is missing
      return !this.columnMapping.description || !this.columnMapping.amount;
    }
  },
  methods: {
    handleDrop(e) {
      this.isDragging = false;
      const files = e.dataTransfer.files;
      if (files.length) {
        this.processFile(files[0]);
      }
    },
    handleFileSelect(e) {
      const files = e.target.files;
      if (files.length) {
        this.processFile(files[0]);
      }
    },
    processFile(file) {
      // Only accept CSV files
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        this.error = 'Please upload a CSV file.';
        return;
      }
      
      this.selectedFile = file;
      this.error = null;
      
      // Parse CSV to preview and extract headers
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (results.errors && results.errors.length) {
            this.error = `Error parsing CSV: ${results.errors[0].message}`;
            return;
          }
          
          this.csvData = results.data;
          this.csvHeaders = results.meta.fields;
          
          // Try to auto-detect column mappings
          this.autoDetectColumns();
        },
        error: (error) => {
          this.error = `Error reading CSV: ${error}`;
        }
      });
    },
    autoDetectColumns() {
      // Auto-detect description column
      const descriptionKeywords = ['description', 'desc', 'transaction', 'details', 'memo', 'notes'];
      const amountKeywords = ['amount', 'price', 'payment', 'cost', 'total', 'value'];
      
      // Find potential description column
      for (const header of this.csvHeaders) {
        const headerLower = header.toLowerCase();
        if (descriptionKeywords.some(keyword => headerLower.includes(keyword))) {
          this.columnMapping.description = header;
          break;
        }
      }
      
      // Find potential amount column
      for (const header of this.csvHeaders) {
        const headerLower = header.toLowerCase();
        if (amountKeywords.some(keyword => headerLower.includes(keyword))) {
          this.columnMapping.amount = header;
          break;
        }
      }
    },
    removeFile() {
      this.selectedFile = null;
      this.csvData = null;
      this.csvHeaders = [];
      this.columnMapping = {
        description: '',
        amount: ''
      };
      this.error = null;
    },
    async importExpenses() {
      if (!this.csvData || !this.columnMapping.description || !this.columnMapping.amount) {
        return;
      }
      
      this.isProcessing = true;
      this.error = null;
      
      try {
        // Map CSV data to expenses
        const expenses = this.csvData.map(row => {
          const description = row[this.columnMapping.description];
          const amountStr = row[this.columnMapping.amount].replace(/[^\d.-]/g, '');
          const amount = parseFloat(amountStr);
          
          if (!description || isNaN(amount)) {
            return null;
          }
          
          return {
            description: description,
            amount: Math.abs(amount) // Use absolute value for now
          };
        }).filter(expense => expense !== null);
        
        if (expenses.length === 0) {
          throw new Error('No valid expenses found in the CSV.');
        }
        
        // Send to backend
        const response = await axios.post(`${API_URL}/import_expenses/`, expenses);
        
        // Calculate import summary
        this.importedCount = response.data.length;
        this.importTotal = expenses.reduce((sum, expense) => sum + expense.amount, 0);
        
        // Show success state
        this.isSuccess = true;
        
        // Emit event for parent component to refresh expenses
        this.$emit('import-complete');
        
      } catch (error) {
        console.error('Error importing expenses:', error);
        this.error = error.response?.data?.detail || error.message || 'Failed to import expenses';
      } finally {
        this.isProcessing = false;
      }
    },
    resetImport() {
      this.selectedFile = null;
      this.csvData = null;
      this.csvHeaders = [];
      this.columnMapping = {
        description: '',
        amount: ''
      };
      this.isSuccess = false;
      this.error = null;
    }
  }
}
</script>

<style scoped>
.csv-import-section {
  margin-bottom: 2rem;
}

.upload-form {
  display: flex;
  flex-direction: column;
}

.import-description {
  margin-bottom: 1rem;
  color: #4a5568;
}

.upload-container {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  background-color: #f9fafc;
  transition: all 0.2s;
  margin-bottom: 1.5rem;
  cursor: pointer;
}

.upload-container:hover {
  border-color: #3b82f6;
  background-color: #f0f7ff;
}

.drag-over {
  border-color: #3b82f6;
  background-color: #ebf5ff;
}

.upload-icon {
  width: 3rem;
  height: 3rem;
  color: #6b7280;
  margin-bottom: 1rem;
}

.upload-text {
  margin-bottom: 0.5rem;
  color: #4a5568;
}

.upload-prompt {
  display: block;
  margin-bottom: 0.5rem;
}

.file-select-button {
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s;
  display: inline-block;
}

.file-select-button:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.hidden-file-input {
  display: none;
}

.file-format-note {
  font-size: 0.875rem;
  color: #9ca3af;
}

.selected-file {
  margin-top: 1.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background-color: #f3f4f6;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.file-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #4b5563;
  margin-right: 0.5rem;
}

.file-name {
  flex: 1;
  font-size: 0.875rem;
  color: #374151;
}

.remove-file-button {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1rem;
  line-height: 1;
  border-radius: 9999px;
  transition: all 0.2s;
}

.remove-file-button:hover {
  background-color: #e5e7eb;
  color: #4b5563;
}

.mapping-options {
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e5e7eb;
}

.mapping-title {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.mapping-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 1rem;
}

.mapping-form {
  display: grid;
  gap: 1rem;
}

.mapping-group {
  display: flex;
  flex-direction: column;
}

.mapping-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
  margin-bottom: 0.375rem;
}

.mapping-select {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background-color: white;
  color: #1f2937;
  transition: all 0.2s;
}

.mapping-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}

.import-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.import-button:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.import-button:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

.processing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.75rem;
}

.processing-text {
  color: #6b7280;
}

.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
}

.success-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  background-color: #dcfce7;
  border-radius: 9999px;
  margin-bottom: 1.5rem;
}

.success-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: #16a34a;
}

.success-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.success-message {
  text-align: center;
  color: #4b5563;
  margin-bottom: 1.5rem;
}

.import-summary {
  width: 100%;
  background-color: #f9fafb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-label {
  font-weight: 500;
  color: #4b5563;
}

.summary-value {
  font-weight: 600;
  color: #1f2937;
}

.done-button {
  padding: 0.75rem 2rem;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.done-button:hover {
  background-color: #1d4ed8;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 0;
}

.error-message {
  color: #b91c1c;
  text-align: center;
  margin-bottom: 1.5rem;
}

.retry-button {
  padding: 0.75rem 2rem;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-button:hover {
  background-color: #1d4ed8;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>