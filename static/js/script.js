// Global variables
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let isListening = false;
let speechRecognition = null;
let currentStep = 'product';
let ttsEnabled = true;

// Audio recording configuration
const audioConfig = {
    type: 'audio/webm;codecs=opus',
    sampleRate: 16000,
    channelCount: 1,
    bitsPerSecond: 16000
};

document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('user-input')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    document.querySelector('.chat-send')?.addEventListener('click', sendMessage);
    
    setupSpeechRecognition();
    
    // Add event listener for record button
    document.getElementById('recordButton')?.addEventListener('click', toggleRecording);
    
    // Init keywords display
    initKeywordsDisplay();
});

// Initialize keywords display
function initKeywordsDisplay() {
    // Default keywords
    const defaultKeywords = ["B2B Sales", "AI Assistant", "Lead Generation"];
    updateKeywords(defaultKeywords);
}

// Function to send a message
function sendMessage() {
    const userInput = document.getElementById('user-input')?.value.trim();
    if (!userInput) return;
    
    // Clear the input field
    document.getElementById('user-input').value = "";
    
    // Add user message to chat
    addMessageToChat('user', userInput);
    
    // Process the message
    processUserInput(userInput);
}

// Process user input
function processUserInput(text) {
    // Get the current step
    const step = document.getElementById('current-step')?.value || 'product';
    
    // Show processing indicator
    addMessageToChat('assistant', '<em>Processing...</em>', 'processing-message');
    
    // Call the voice interaction API
    fetch('/api/voice_interaction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            step: step
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove processing indicator
        removeProcessingMessage();
        
        if (data.success) {
            // Add the assistant's message to the chat
            addMessageToChat('assistant', data.text);
            
            // Update the current step if provided
            if (data.next_step) {
                if (document.getElementById('current-step')) {
                    document.getElementById('current-step').value = data.next_step;
                }
                currentStep = data.next_step;
                updateProgressIndicator(data.next_step);
            }
            
            // Update keywords if provided
            if (data.keywords && data.keywords.length > 0) {
                updateKeywords(data.keywords);
            }
            
            // Play audio response if available
            if (data.audio && ttsEnabled) {
                playAudioResponse(data.audio);
            }
            
            // Check if recommendations are ready
            if (data.completed || data.show_recommendations_tab) {
                showRecommendationsButton();
            }
        } else {
            console.error("Error processing input:", data.error);
            addMessageToChat('assistant', "I'm sorry, there was an error. Please try again.");
        }
    })
    .catch(error => {
        // Remove processing indicator
        removeProcessingMessage();
        
        console.error('Error processing input:', error);
        addMessageToChat('assistant', "I'm sorry, there was an error. Please try again.");
    });
}

// Remove processing message
function removeProcessingMessage() {
    const processingMessage = document.querySelector('.processing-message');
    if (processingMessage) {
        processingMessage.remove();
    }
}

// Initialize speech recognition
function setupSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = true;
        speechRecognition.lang = 'en-US';
        
        speechRecognition.onstart = function() {
            isListening = true;
            
            // Visual feedback when recording
            const recordButton = document.getElementById('recordButton');
            if (recordButton) {
                recordButton.classList.add('recording');
                recordButton.classList.add('bg-red-500');
                recordButton.classList.remove('bg-blue-500');
            }
        };
        
        speechRecognition.onresult = function(event) {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            
            // Update input field with transcript
            const userInput = document.getElementById('user-input');
            if (userInput) {
                userInput.value = finalTranscript || interimTranscript;
            }
        };
        
        speechRecognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            isListening = false;
            
            // Reset visual feedback
            const recordButton = document.getElementById('recordButton');
            if (recordButton) {
                recordButton.classList.remove('recording');
                recordButton.classList.remove('bg-red-500');
                recordButton.classList.add('bg-blue-500');
            }
        };
        
        speechRecognition.onend = function() {
            isListening = false;
            
            // Reset visual feedback
            const recordButton = document.getElementById('recordButton');
            if (recordButton) {
                recordButton.classList.remove('recording');
                recordButton.classList.remove('bg-red-500');
                recordButton.classList.add('bg-blue-500');
            }
            
            // Submit the transcript if available
            const userInput = document.getElementById('user-input');
            if (userInput && userInput.value.trim()) {
                sendMessage();
            }
        };
    } else {
        console.error('Speech recognition not supported in this browser');
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.disabled = true;
            recordButton.title = "Speech recognition not supported in this browser";
        }
    }
}

// Toggle recording
function toggleRecording() {
    if (isListening) {
        stopRecording();
    } else {
        startRecording();
    }
}

// Start recording
function startRecording() {
    if (speechRecognition) {
        try {
            speechRecognition.start();
        } catch (e) {
            console.error('Error starting speech recognition:', e);
        }
    } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Fallback to MediaRecorder if SpeechRecognition is not available
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = () => {
                    processAudio();
                };
                
                audioChunks = [];
                mediaRecorder.start();
                isRecording = true;
                
                // Visual feedback when recording
                const recordButton = document.getElementById('recordButton');
                if (recordButton) {
                    recordButton.classList.add('recording');
                    recordButton.classList.add('bg-red-500');
                    recordButton.classList.remove('bg-blue-500');
                }
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Microphone access denied. Please check your browser permissions.');
            });
    }
}

// Stop recording
function stopRecording() {
    if (speechRecognition && isListening) {
        try {
            speechRecognition.stop();
        } catch (e) {
            console.error('Error stopping speech recognition:', e);
        }
    } else if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Reset visual feedback
        const recordButton = document.getElementById('recordButton');
        if (recordButton) {
            recordButton.classList.remove('recording');
            recordButton.classList.remove('bg-red-500');
            recordButton.classList.add('bg-blue-500');
        }
    }
}

// Process audio recording (for MediaRecorder fallback)
async function processAudio() {
    try {
        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: audioConfig.type });
        
        // Create FormData
        const formData = new FormData();
        formData.append('audio', audioBlob);
        
        // Add the current step
        const step = document.getElementById('current-step')?.value || 'product';
        formData.append('step', step);
        
        // Send audio to server
        const response = await fetch('/api/process_audio', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Add user message with transcription
            addMessageToChat('user', data.transcript);
            
            // Process the response
            if (data.response) {
                // Add assistant message
                addMessageToChat('assistant', data.response.text);
                
                // Update step if needed
                if (data.response.next_step) {
                    if (document.getElementById('current-step')) {
                        document.getElementById('current-step').value = data.response.next_step;
                    }
                    currentStep = data.response.next_step;
                    updateProgressIndicator(data.response.next_step);
                }
                
                // Update keywords if provided
                if (data.response.keywords && data.response.keywords.length > 0) {
                    updateKeywords(data.response.keywords);
                }
                
                // Play audio response if available
                if (data.response.audio && ttsEnabled) {
                    playAudioResponse(data.response.audio);
                }
            }
        } else {
            console.error('Error processing audio:', data.error);
            addMessageToChat('assistant', "I'm sorry, I couldn't understand what you said. Please try again.");
        }
    } catch (error) {
        console.error('Error processing audio:', error);
        addMessageToChat('assistant', "I'm sorry, there was an error processing your voice input. Please try typing instead.");
    }
}

// Add message to chat
function addMessageToChat(role, message, className = '') {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-4 flex justify-${role === 'user' ? 'end' : 'start'} ${className}`;
    
    const bubble = document.createElement('div');
    bubble.className = `max-w-sm rounded-2xl px-4 py-3 ${role === 'user' ? 'bg-blue-500' : 'bg-gray-800'} text-white`;
    bubble.innerHTML = message; // Using innerHTML to support HTML in messages (like processing indicator)
    
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to the latest message
    const container = document.querySelector('.overflow-y-auto');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Play audio response
function playAudioResponse(audioBase64) {
    const audio = document.getElementById('audio-response');
    if (!audio) return;
    
    audio.src = `data:audio/mpeg;base64,${audioBase64}`;
    audio.play().catch(e => console.error('Error playing audio:', e));
}

// Update keywords
function updateKeywords(keywords) {
    if (!keywords || !Array.isArray(keywords) || keywords.length === 0) {
        return;
    }
    
    const keywordsContainer = document.getElementById('keywordsContainer');
    if (!keywordsContainer) return;
    
    // Clear existing keywords
    keywordsContainer.innerHTML = '';
    
    // Add new keywords with animation
    keywords.forEach((keyword, index) => {
        const span = document.createElement('span');
        span.className = 'bg-gradient-to-r from-blue-500/20 to-teal-400/20 text-blue-300 px-3 py-1 rounded-full text-sm keyword-animate';
        span.style.animationDelay = `${index * 0.1}s`;
        span.textContent = keyword;
        keywordsContainer.appendChild(span);
    });
}

// Update progress indicator
function updateProgressIndicator(step) {
    const dots = document.querySelectorAll('.progress-dot');
    dots.forEach(dot => {
        dot.classList.remove('active');
        if (dot.dataset.step === step) {
            dot.classList.add('active');
        }
    });
}

// Show recommendations button
function showRecommendationsButton() {
    // Redirect to recommendations page or show a button
    if (confirm('Your recommendations are ready! Would you like to view them now?')) {
        window.location.href = '/recommendations';
    }
}

// Toggle text-to-speech
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    
    // Update UI to reflect TTS state
    const ttsToggle = document.getElementById('tts-toggle');
    if (ttsToggle) {
        ttsToggle.innerHTML = ttsEnabled 
            ? '<i class="fas fa-volume-up"></i>' 
            : '<i class="fas fa-volume-mute"></i>';
        ttsToggle.title = ttsEnabled ? 'Voice on (click to turn off)' : 'Voice off (click to turn on)';
    }
}