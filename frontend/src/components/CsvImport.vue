// CsvImport.vue
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
          <div class="mapping-options">
            <h3 class="mapping-title">Column Mapping</h3>
            <p class="mapping-description">
              Please match your CSV columns to our expense fields:
            </p>
            
            <div class="mapping-form">
              <div class="mapping-group">
                <label class="mapping-label">Date Column:</label>
                <select v-model="columnMapping.date" class="mapping-select">
                  <option v-for="header in csvHeaders" :key="header" :value="header">
                    {{ header }}
                  </option>
                </select>
              </div>
              
              <div class="mapping-group">
                <label class="mapping-label">Description Column:</label>
                <select v-model="columnMapping.description" class="mapping-select">
                  <option v-for="header in csvHeaders" :key="header" :value="header">
                    {{ header }}
                  </option>
                </select>
              </div>
              
              <div class="mapping-group">
                <label class="mapping-label">Amount Column:</label>
                <select v-model="columnMapping.amount" class="mapping-select">
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
          <div class="summary-item">
            <span class="summary-label">Date Range:</span>
            <span class="summary-value">{{ importDateRange }}</span>
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
        date: '',
        description: '',
        amount: ''
      },
      isProcessing: false,
      isSuccess: false,
      importedCount: 0,
      importTotal: 0,
      importDateRange: '',
      error: null
    };
  },
  computed: {
    isImportButtonDisabled() {
      // Disable import button if any mapping is missing
      return !this.columnMapping.date || 
             !this.columnMapping.description || 
             !this.columnMapping.amount;
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
          if (results.errors.length) {
            this.error = `Error parsing CSV: ${results.errors[0].message}`;
            return;
          }
          
          this.csvData = results.data;
          this.csvHeaders = results.meta.fields;
          
          // Try to auto-detect column mappings
          this.autoDetectColumns();
        },
        error: (error) => {
          this.error = `Error reading CSV