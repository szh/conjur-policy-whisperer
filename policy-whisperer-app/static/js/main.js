document.addEventListener('DOMContentLoaded', function() {
    // Initialize highlight.js
    hljs.highlightAll();
    
    // DOM elements
    const policyForm = document.getElementById('policyForm');
    const generateBtn = document.getElementById('generateBtn');
    const policyOutput = document.getElementById('policyOutput');
    const policyExplanation = document.getElementById('policyExplanation');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const copyBtn = document.getElementById('copyBtn');
    const createPrBtn = document.getElementById('createPrBtn');
    const connectRepoBtn = document.getElementById('connectRepo');
    const repoUrlInput = document.getElementById('repoUrl');
    const repoStatus = document.getElementById('repoStatus');
    const targetPathInput = document.getElementById('targetPath');
    const filePathDisplay = document.getElementById('filePathDisplay');
    const targetFilePath = document.getElementById('targetFilePath');
    const editPathBtn = document.getElementById('editPathBtn');
    const editPolicyBtn = document.getElementById('editPolicyBtn');
    const savePolicyBtn = document.getElementById('savePolicyBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const policyEditor = document.getElementById('policyEditor');
    const policyContainer = document.getElementById('policyContainer');
    
    // GitHub repository connection state
    let connectedRepo = {
        url: 'https://github.com/szh/conjur-policy-whisperer-demo',
        owner: 'szh',
        name: 'conjur-policy-whisperer-demo',
        connected: true
    };
    
    // Connect to GitHub repository
    connectRepoBtn.addEventListener('click', function() {
        const repoUrl = repoUrlInput.value.trim();
        if (!repoUrl) {
            alert('Please enter a valid GitHub repository URL');
            return;
        }
        
        // Show loading state
        connectRepoBtn.disabled = true;
        connectRepoBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Connecting...';
        
        // For demo purposes, simulate API call with timeout
        setTimeout(() => {
            // Parse repo URL to extract owner and name
            const urlParts = repoUrl.split('/');
            const repoOwner = urlParts[urlParts.length - 2];
            const repoName = urlParts[urlParts.length - 1];
            
            // Update connected repo state
            connectedRepo = {
                url: repoUrl,
                owner: repoOwner,
                name: repoName,
                connected: true
            };
            
            // Update UI
            repoStatus.innerHTML = `<i class="bi bi-check-circle-fill"></i> Connected to repository: <strong>${repoOwner}/${repoName}</strong>`;
            repoStatus.classList.remove('alert-danger', 'd-none');
            repoStatus.classList.add('alert-success');
            
            // Reset button state
            connectRepoBtn.disabled = false;
            connectRepoBtn.textContent = 'Connect';
        }, 1500);
    });
    
    // Edit file path button
    editPathBtn.addEventListener('click', function() {
        const currentPath = targetFilePath.textContent;
        targetPathInput.value = currentPath;
        targetPathInput.focus();
    });
    
    // Policy editing functionality
    editPolicyBtn.addEventListener('click', function() {
        // Switch to edit mode
        policyEditor.value = policyOutput.textContent;
        policyOutput.parentElement.classList.add('d-none');
        policyEditor.classList.remove('d-none');
        
        // Show/hide appropriate buttons
        editPolicyBtn.classList.add('d-none');
        savePolicyBtn.classList.remove('d-none');
        cancelEditBtn.classList.remove('d-none');
        createPrBtn.disabled = true;
    });
    
    savePolicyBtn.addEventListener('click', function() {
        // Save the edited policy
        const editedPolicy = policyEditor.value;
        policyOutput.textContent = editedPolicy;
        hljs.highlightElement(policyOutput);
        
        // Switch back to view mode
        policyEditor.classList.add('d-none');
        policyOutput.parentElement.classList.remove('d-none');
        
        // Show/hide appropriate buttons
        savePolicyBtn.classList.add('d-none');
        cancelEditBtn.classList.add('d-none');
        editPolicyBtn.classList.remove('d-none');
        createPrBtn.disabled = false;
    });
    
    cancelEditBtn.addEventListener('click', function() {
        // Cancel editing without saving changes
        policyEditor.classList.add('d-none');
        policyOutput.parentElement.classList.remove('d-none');
        
        // Show/hide appropriate buttons
        savePolicyBtn.classList.add('d-none');
        cancelEditBtn.classList.add('d-none');
        editPolicyBtn.classList.remove('d-none');
        createPrBtn.disabled = false;
    });
    
    // Create PR button
    createPrBtn.addEventListener('click', function() {
        if (!connectedRepo.connected) {
            alert('Please connect to a GitHub repository first');
            return;
        }
        
        const path = targetFilePath.textContent;
        const content = policyOutput.textContent;
        
        // Show loading state
        createPrBtn.disabled = true;
        createPrBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating PR...';
        
        // Create notification area above the policy explanation
        const notificationArea = document.createElement('div');
        notificationArea.id = 'prNotificationArea';
        notificationArea.className = 'mb-3';
        policyContainer.insertAdjacentElement('beforebegin', notificationArea);
        
        // Call the API endpoint to create a PR
        fetch('/api/create-pr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                repository: `${connectedRepo.owner}/${connectedRepo.name}`,
                file_path: path,
                content: content,
                commit_message: `Add Conjur policy: ${path}`
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message above the policy using the API response
                notificationArea.innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="bi bi-check-circle-fill"></i> Pull Request Created</h6>
                    <p>Your policy has been submitted as a pull request to <strong>${connectedRepo.owner}/${connectedRepo.name}</strong>.</p>
                    <p>PR #${data.pr_number}: <a href="${data.pr_url}" target="_blank">${path}</a></p>
                    <p class="text-muted small">${data.message}</p>
                </div>`;
            } else {
                // Show error message
                notificationArea.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="bi bi-exclamation-triangle-fill"></i> Error Creating PR</h6>
                    <p>${data.error || 'An unknown error occurred'}</p>
                </div>`;
            }
            
            // Reset button state
            createPrBtn.disabled = false;
            createPrBtn.textContent = 'Create PR';
        })
        .catch(error => {
            // Handle network or other errors
            notificationArea.innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="bi bi-exclamation-triangle-fill"></i> Error Creating PR</h6>
                <p>Failed to connect to the server: ${error.message}</p>
            </div>`;
            
            // Reset button state
            createPrBtn.disabled = false;
            createPrBtn.textContent = 'Create PR';
        });
    });
    
    policyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const prompt = document.getElementById('prompt').value;
        const policyType = 'general'; // Always use 'general' as the type and let the backend detect the appropriate type
        const targetPath = targetPathInput.value.trim() || ''; // Get target file path if specified
        
        if (!prompt.trim()) {
            alert('Please describe what policy you need');
            return;
        }
        
        if (!connectedRepo.connected) {
            alert('Please connect to a GitHub repository first');
            return;
        }
        
        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        filePathDisplay.classList.add('d-none');
        policyOutput.textContent = '';
        policyExplanation.innerHTML = '<p class="text-muted">Analyzing your request...</p>';
        generateBtn.disabled = true;
        copyBtn.disabled = true;
        createPrBtn.disabled = true;
        
        // Send API request
        fetch('/api/generate-policy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                policy_type: policyType,
                target_path: targetPath,
                repository: `${connectedRepo.owner}/${connectedRepo.name}`
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            generateBtn.disabled = false;
            
            if (data.success) {
                // Display the generated policy
                policyOutput.textContent = data.policy;
                hljs.highlightElement(policyOutput);
                
                // Enable buttons
                copyBtn.disabled = false;
                createPrBtn.disabled = false;
                editPolicyBtn.classList.remove('d-none');
                
                // Show file path
                const suggestedPath = data.suggested_path || targetPath || 'policy.yml';
                targetFilePath.textContent = suggestedPath;
                filePathDisplay.classList.remove('d-none');
                
                // Clear any previous PR notifications
                const existingNotification = document.getElementById('prNotificationArea');
                if (existingNotification) {
                    existingNotification.remove();
                }
                
                // Display the explanation from the API
                if (data.explanation) {
                    displayExplanation(data.explanation, data.resources);
                    
                    // Add repository context to explanation
                    // policyExplanation.innerHTML += `
                    // <div class="mt-3">
                    //     <h6>Repository Context</h6>
                    //     <p>This policy is recommended for your repository <strong>${connectedRepo.owner}/${connectedRepo.name}</strong>.</p>
                    //     <p>To apply this policy, click the <strong>Create PR</strong> button above.</p>
                    // </div>`;
                } else {
                    // Fallback to client-side explanation if server didn't provide one
                    generateExplanation(data.policy);
                }
            } else {
                policyOutput.textContent = `Error: ${data.error}`;
                policyExplanation.innerHTML = '<p class="text-danger">Failed to generate policy recommendation.</p>';
            }
        })
        .catch(error => {
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            generateBtn.disabled = false;
            
            // Display error
            policyOutput.textContent = `Error: ${error.message}`;
            policyExplanation.innerHTML = '<p class="text-danger">Failed to generate policy explanation.</p>';
        });
    });
    
    // Example buttons
    const exampleButtons = document.querySelectorAll('.use-example');
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const example = this.getAttribute('data-example');
            
            document.getElementById('prompt').value = example;
            
            // Scroll to form
            document.getElementById('prompt').scrollIntoView({ behavior: 'smooth' });
        });
    });
    
    // Copy button
    copyBtn.addEventListener('click', function() {
        const policyText = policyOutput.textContent;
        navigator.clipboard.writeText(policyText)
            .then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy: ', err);
                alert('Failed to copy policy to clipboard');
            });
    });
    
    // Function to display the explanation from the API
    function displayExplanation(explanation, resources) {
        try {
            // Clean up the explanation text to handle inconsistent formatting
            let cleanExplanation = explanation;
            
            // Check if the explanation is wrapped in markdown code blocks
            if (cleanExplanation.trim().startsWith('```markdown') || 
                cleanExplanation.trim().startsWith('```md')) {
                // Extract content between markdown code blocks
                const match = cleanExplanation.match(/```(?:markdown|md)\s*([\s\S]*?)```/);
                if (match && match[1]) {
                    cleanExplanation = match[1].trim();
                }
            } else if (cleanExplanation.trim().startsWith('```') && 
                       cleanExplanation.trim().endsWith('```')) {
                // Extract content between generic code blocks
                cleanExplanation = cleanExplanation.replace(/^```[\s\S]*?\n/, '').replace(/```$/, '');
            }
            
            // Render the cleaned markdown explanation
            const renderedExplanation = marked.parse(cleanExplanation);
            
            // Create a styled container for the markdown explanation
            let html = `<div class="markdown-explanation">${renderedExplanation}</div>`;
            
            // Add resource summary if available
            // if (resources) {
            //     const resourceTypes = Object.keys(resources).filter(type => resources[type] > 0);
                
            //     if (resourceTypes.length > 0) {
            //         html += '<div class="mt-3"><h6>Resource Summary</h6>';
            //         html += '<ul class="resource-list">';
            //         resourceTypes.forEach(type => {
            //             html += `<li><span class="badge bg-primary me-2">${resources[type]}</span><strong>${type}</strong>: ${getResourceTypeDescription(type)}</li>`;
            //         });
            //         html += '</ul></div>';
            //     }
            // }
            
            // Add usage instructions
            // html += '<div class="mt-3"><h6>Usage Instructions</h6>';
            // html += '<p>To load this policy into Conjur, save it as a .yml file and use the Conjur CLI:</p>';
            // html += '<pre><code class="language-bash">conjur policy load -b root -f policy-file.yml</code></pre></div>';
            
            policyExplanation.innerHTML = html;
            
            // Highlight any code blocks in the explanation
            policyExplanation.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        } catch (error) {
            console.error('Error rendering markdown explanation:', error);
            policyExplanation.innerHTML = '<p class="text-danger">Failed to render policy explanation.</p>';
        }
    }
    
    // Fallback function to generate policy explanation client-side
    function generateExplanation(policy) {
        try {
            // Parse the YAML to get some basic info
            const lines = policy.split('\n');
            const resourceTypes = [];
            
            for (const line of lines) {
                if (line.includes('!policy')) resourceTypes.push('policy');
                if (line.includes('!user')) resourceTypes.push('user');
                if (line.includes('!host')) resourceTypes.push('host');
                if (line.includes('!group')) resourceTypes.push('group');
                if (line.includes('!variable')) resourceTypes.push('variable');
                if (line.includes('!grant')) resourceTypes.push('grant');
                if (line.includes('!permit')) resourceTypes.push('permit');
                if (line.includes('!webservice')) resourceTypes.push('webservice');
            }
            
            // Remove duplicates
            const uniqueResourceTypes = [...new Set(resourceTypes)];
            
            let explanation = '<h6>Policy Overview</h6>';
            explanation += '<p>This policy contains the following resource types:</p>';
            
            if (uniqueResourceTypes.length > 0) {
                explanation += '<ul>';
                uniqueResourceTypes.forEach(type => {
                    explanation += `<li><strong>${type}</strong>: ${getResourceTypeDescription(type)}</li>`;
                });
                explanation += '</ul>';
            } else {
                explanation += '<p>No specific resource types identified.</p>';
            }
            
            explanation += '<h6>Usage Instructions</h6>';
            explanation += '<p>To load this policy into Conjur, save it as a .yml file and use the Conjur CLI:</p>';
            explanation += '<pre><code class="language-bash">conjur policy load -b root -f policy-file.yml</code></pre>';
            
            policyExplanation.innerHTML = explanation;
            
            // Highlight any code blocks
            policyExplanation.querySelectorAll('pre code').forEach(block => {
                hljs.highlightElement(block);
            });
        } catch (error) {
            policyExplanation.innerHTML = '<p>Unable to generate detailed explanation for this policy.</p>';
        }
    }
    
    // Helper function for resource type descriptions
    function getResourceTypeDescription(type) {
        const descriptions = {
            'policy': 'A container for Conjur resources that provides a namespace and access control',
            'user': 'A human user of the system',
            'host': 'A non-human identity, typically an application or machine',
            'group': 'A collection of users and/or hosts',
            'variable': 'A secret value stored in Conjur',
            'grant': 'Assigns roles to members, granting them permissions',
            'permit': 'Defines permissions on resources',
            'webservice': 'Defines a web service that can be authenticated to'
        };
        
        return descriptions[type] || 'A Conjur resource';
    }
    
    // No need to fetch policy types anymore as we're using automatic detection
});
