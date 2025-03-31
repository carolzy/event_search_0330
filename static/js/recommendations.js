{% extends "base.html" %}

{% block title %}Carol.ai - Your Perfect Customer Recommendations{% endblock %}

{% block styles %}
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
        theme: {
            extend: {
                colors: {
                    blue: {
                        500: '#3B82F6',
                    },
                    teal: {
                        400: '#2DD4BF',
                    },
                }
            }
        }
    }
</script>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    
    .bg-clip-text {
        -webkit-background-clip: text;
        background-clip: text;
    }
    
    .text-transparent {
        color: transparent;
    }
</style>
{% endblock %}

{% block content %}
<div class="bg-black text-white min-h-screen">
    <!-- Navigation -->
    <nav class="border-b border-gray-800 bg-black">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16 items-center">
                <div class="flex-shrink-0 flex items-center">
                    <span class="text-xl font-bold bg-gradient-to-r from-blue-500 to-teal-400 bg-clip-text text-transparent">carol.ai</span>
                </div>
                <div class="hidden md:flex space-x-8">
                    <a href="/" class="text-gray-300 hover:text-white">Home</a>
                    <a href="#recommendations" class="text-gray-300 hover:text-white">Recommendations</a>
                    <a href="#contact" class="text-gray-300 hover:text-white">Contact</a>
                </div>
                <div>
                    <a href="/" class="bg-gradient-to-r from-blue-500 to-teal-400 px-4 py-2 rounded-full text-sm font-medium">
                        Back to Home
                    </a>
                </div>
            </div>
        </div>
    </nav>
    
    <!-- Header section -->
    <section class="pt-16 pb-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center">
                <h1 class="text-4xl font-bold mb-6 bg-gradient-to-r from-blue-500 to-teal-400 bg-clip-text text-transparent">
                    Your Perfect Customer Matches
                </h1>
                <p class="text-lg text-gray-400 max-w-2xl mx-auto mb-8">
                    Based on your input, I've identified these high-value companies that are most likely to need your product.
                </p>
            </div>
        </div>
    </section>
    
    <!-- Loading indicator -->
    <div id="loading-indicator" class="flex flex-col items-center justify-center py-12">
        <div class="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mb-4"></div>
        <p class="text-gray-400">Loading your personalized recommendations...</p>
    </div>
    
    <!-- Tabs navigation -->
    <div id="recommendations-content" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24" style="display: none;">
        <div class="mb-8 border-b border-gray-800">
            <nav class="flex flex-wrap -mb-px">
                <button class="tab-button active mr-8 py-4 px-1 border-b-2 font-medium text-sm border-blue-500 text-white" data-tab="companies">
                    Companies
                </button>
                <button class="tab-button mr-8 py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-400 hover:text-gray-300" data-tab="people">
                    Key People
                </button>
                <button class="tab-button mr-8 py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-400 hover:text-gray-300" data-tab="events">
                    Events
                </button>
                <button class="tab-button py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-400 hover:text-gray-300" data-tab="news">
                    Latest News
                </button>
            </nav>
        </div>
        
        <!-- Companies tab -->
        <div id="companies-tab" class="tab-content active">
            <div id="companies-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Company cards will be inserted here -->
            </div>
            <div id="no-companies" class="bg-gray-800 rounded-lg p-8 text-center" style="display: none;">
                <p class="text-gray-400">No company recommendations available. Please complete the onboarding process first.</p>
                <a href="/" class="inline-block mt-4 bg-gradient-to-r from-blue-500 to-teal-400 px-4 py-2 rounded-full text-sm font-medium">
                    Start Onboarding
                </a>
            </div>
        </div>
        
        <!-- People tab -->
        <div id="people-tab" class="tab-content hidden">
            <div id="people-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- People cards will be inserted here -->
            </div>
            <div id="no-people" class="bg-gray-800 rounded-lg p-8 text-center" style="display: none;">
                <p class="text-gray-400">No key people recommendations available yet.</p>
            </div>
        </div>
        
        <!-- Events tab -->
        <div id="events-tab" class="tab-content hidden">
            <div id="events-grid" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Event cards will be inserted here -->
            </div>
            <div id="no-events" class="bg-gray-800 rounded-lg p-8 text-center" style="display: none;">
                <p class="text-gray-400">No events found in your area.</p>
            </div>
        </div>
        
        <!-- News tab -->
        <div id="news-tab" class="tab-content hidden">
            <div id="news-grid" class="grid grid-cols-1 gap-6">
                <!-- News items will be inserted here -->
            </div>
            <div id="no-news" class="bg-gray-800 rounded-lg p-8 text-center" style="display: none;">
                <p class="text-gray-400">No recent news articles found.</p>
            </div>
        </div>
        
        <!-- Regenerate recommendations button -->
        <div class="mt-12 text-center">
            <button id="regenerate-button" class="bg-gradient-to-r from-blue-500 to-teal-400 px-6 py-3 rounded-full text-white font-medium transition-transform hover:scale-105">
                Regenerate Recommendations
            </button>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    fetchRecommendations();
    
    // Set up tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
                btn.classList.remove('border-blue-500');
                btn.classList.remove('text-white');
                btn.classList.add('border-transparent');
                btn.classList.add('text-gray-400');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            this.classList.add('border-blue-500');
            this.classList.add('text-white');
            this.classList.remove('border-transparent');
            this.classList.remove('text-gray-400');
            
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
                content.classList.remove('active');
            });
            
            // Show the selected tab content
            const tabId = this.getAttribute('data-tab') + '-tab';
            document.getElementById(tabId).classList.remove('hidden');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Set up regenerate button
    document.getElementById('regenerate-button').addEventListener('click', function() {
        fetchRecommendations(true);
    });
});

function fetchRecommendations(regenerate = false) {
    // Show loading indicator
    document.getElementById('loading-indicator').style.display = 'flex';
    document.getElementById('recommendations-content').style.display = 'none';
    
    // Hide all "no data" messages
    document.querySelectorAll('[id^="no-"]').forEach(el => {
        el.style.display = 'none';
    });
    
    // Clear existing content
    document.getElementById('companies-grid').innerHTML = '';
    document.getElementById('people-grid').innerHTML = '';
    document.getElementById('events-grid').innerHTML = '';
    document.getElementById('news-grid').innerHTML = '';
    
    // API endpoint
    const endpoint = regenerate ? '/api/recommendations?regenerate=true' : '/api/recommendations';
    
    // Fetch recommendations
    fetch(endpoint)
        .then(response => response.json())
        .then(recommendations => {
            // Hide loading indicator
            document.getElementById('loading-indicator').style.display = 'none';
            document.getElementById('recommendations-content').style.display = 'block';
            
            // Process recommendations
            if (Array.isArray(recommendations) && recommendations.length > 0) {
                displayRecommendations(recommendations);
            } else {
                // Show no data messages
                document.getElementById('no-companies').style.display = 'block';
                document.getElementById('no-people').style.display = 'block';
                document.getElementById('no-events').style.display = 'block';
                document.getElementById('no-news').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error fetching recommendations:', error);
            
            // Hide loading indicator
            document.getElementById('loading-indicator').style.display = 'none';
            document.getElementById('recommendations-content').style.display = 'block';
            
            // Show error message
            document.getElementById('companies-grid').innerHTML = `
                <div class="col-span-full bg-gray-800 rounded-lg p-8 text-center">
                    <p class="text-red-400">Error loading recommendations. Please try again later.</p>
                </div>
            `;
        });
}

function displayRecommendations(recommendations) {
    // Process companies
    let companyCount = 0;
    let peopleCount = 0;
    let eventsCount = 0;
    let newsCount = 0;
    
    recommendations.forEach(company => {
        // Add to Companies tab
        const companyCard = createCompanyCard(company);
        document.getElementById('companies-grid').appendChild(companyCard);
        companyCount++;
        
        // Process key people
        if (company.leads && Array.isArray(company.leads) && company.leads.length > 0) {
            company.leads.forEach(person => {
                const personCard = createPersonCard(person, company.name);
                document.getElementById('people-grid').appendChild(personCard);
                peopleCount++;
            });
        } else if (company.key_personnel && Array.isArray(company.key_personnel) && company.key_personnel.length > 0) {
            company.key_personnel.forEach(person => {
                // Handle string format: "Name, Title"
                let name, title;
                if (typeof person === 'string') {
                    const parts = person.split(',');
                    name = parts[0].trim();
                    title = parts.length > 1 ? parts.slice(1).join(',').trim() : '';
                } else {
                    name = person.name || 'Unknown';
                    title = person.title || '';
                }
                
                const personCard = createPersonCard({name, title}, company.name);
                document.getElementById('people-grid').appendChild(personCard);
                peopleCount++;
            });
        }
        
        // Process events
        if (company.events && Array.isArray(company.events) && company.events.length > 0) {
            company.events.forEach(event => {
                if (event.name !== 'No upcoming events') {
                    const eventCard = createEventCard(event, company.name);
                    document.getElementById('events-grid').appendChild(eventCard);
                    eventsCount++;
                }
            });
        }
        
        // Process news
        if (company.articles && Array.isArray(company.articles) && company.articles.length > 0) {
            company.articles.forEach(article => {
                const newsCard = createNewsCard(article, company.name);
                document.getElementById('news-grid').appendChild(newsCard);
                newsCount++;
            });
        } else if (company.recent_news && Array.isArray(company.recent_news) && company.recent_news.length > 0) {
            company.recent_news.forEach(article => {
                const newsCard = createNewsCard(article, company.name);
                document.getElementById('news-grid').appendChild(newsCard);
                newsCount++;
            });
        }
    });
    
    // Show "no data" messages if needed
    if (companyCount === 0) document.getElementById('no-companies').style.display = 'block';
    if (peopleCount === 0) document.getElementById('no-people').style.display = 'block';
    if (eventsCount === 0) document.getElementById('no-events').style.display = 'block';
    if (newsCount === 0) document.getElementById('no-news').style.display = 'block';
}

function createCompanyCard(company) {
    const div = document.createElement('div');
    div.className = 'bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-500 transition-all duration-300';
    
    // Prepare fit score display if available
    let fitScoreHtml = '';
    if (company.fit_score) {
        const overallScore = company.fit_score.overall_score || 75;
        fitScoreHtml = `
            <div class="mt-4 mb-2">
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-400">Match Score</span>
                    <span class="text-sm font-medium text-blue-400">${Math.round(overallScore)}%</span>
                </div>
                <div class="w-full bg-gray-700 rounded-full h-2 mt-1">
                    <div class="bg-gradient-to-r from-blue-500 to-teal-400 rounded-full h-2" style="width: ${overallScore}%"></div>
                </div>
            </div>
        `;
    }
    
    // Prepare website button
    const websiteUrl = company.website || `https://www.google.com/search?q=${encodeURIComponent(company.name + ' company')}`;
    
    div.innerHTML = `
        <div class="p-6">
            <h3 class="text-xl font-semibold mb-2">${company.name}</h3>
            <p class="text-gray-400 text-sm mb-4">${company.industry || company.description || 'No description available'}</p>
            
            ${company.description && company.description !== company.industry ? `<p class="text-gray-300 mb-4">${company.description}</p>` : ''}
            
            ${company.fit_reason ? `<p class="text-gray-300 mb-4"><span class="text-blue-400 font-medium">Perfect fit because:</span> ${company.fit_reason}</p>` : ''}
            
            ${fitScoreHtml}
            
            <div class="mt-6 flex flex-wrap gap-2">
                <a href="${websiteUrl}" target="_blank" class="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                    Website
                </a>
                <a href="https://www.linkedin.com/search/results/companies/?keywords=${encodeURIComponent(company.name)}" target="_blank" class="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                    </svg>
                    LinkedIn
                </a>
            </div>
        </div>
    `;
    
    return div;
}

function createPersonCard(person, companyName) {
    const div = document.createElement('div');
    div.className = 'bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-500 transition-all duration-300';
    
    // Get person details
    const name = person.name || 'Unknown';
    const title = person.title || '';
    const email = person.email || '';
    const linkedin = person.linkedin || `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(name + ' ' + companyName)}`;
    
    div.innerHTML = `
        <div class="p-6">
            <h3 class="text-xl font-semibold mb-1">${name}</h3>
            <p class="text-blue-400 text-sm mb-3">${title} at ${companyName}</p>
            
            ${email ? `
            <div class="flex items-center text-gray-300 mb-2 text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                ${email}
            </div>
            ` : ''}
            
            <div class="mt-6">
                <a href="${linkedin}" target="_blank" class="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                    </svg>
                    View Profile
                </a>
            </div>
        </div>
    `;
    
    return div;
}

function createEventCard(event, companyName) {
    const div = document.createElement('div');
    div.className = 'bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-500 transition-all duration-300';
    
    // Process event data
    const name = event.name || 'Unnamed Event';
    const date = event.date || 'TBD';
    const location = event.location || 'Location not specified';
    const description = event.description || '';
    const url = event.url || `https://www.google.com/search?q=${encodeURIComponent(name + ' event')}`;
    
    div.innerHTML = `
        <div class="p-6">
            <div class="flex justify-between items-start mb-3">
                <h3 class="text-xl font-semibold">${name}</h3>
                <span class="bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full text-xs">${date}</span>
            </div>
            
            <p class="text-gray-400 text-sm mb-3">Relevant to: ${companyName}</p>
            
            <div class="flex items-center text-gray-300 mb-4 text-sm">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                ${location}
            </div>
            
            ${description ? `<p class="text-gray-300 mb-4">${description}</p>` : ''}
            
            <div class="mt-4">
                <a href="${url}" target="_blank" class="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Event Details
                </a>
            </div>
        </div>
    `;
    
    return div;
}

function createNewsCard(article, companyName) {
    const div = document.createElement('div');
    div.className = 'bg-gray-800 rounded-xl overflow-hidden border border-gray-700 hover:border-blue-500 transition-all duration-300';
    
    // Process article data
    const title = article.title || 'Untitled Article';
    const date = article.date || '';
    const source = article.source || '';
    const summary = article.summary || article.quote || '';
    const url = article.url || `https://www.google.com/search?q=${encodeURIComponent(title + ' ' + companyName)}`;
    
    div.innerHTML = `
        <div class="p-6">
            <div class="flex justify-between items-start mb-3">
                <h3 class="text-xl font-semibold">${title}</h3>
                ${date ? `<span class="bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full text-xs">${date}</span>` : ''}
            </div>
            
            <p class="text-gray-400 text-sm mb-3">
                ${source ? `Source: ${source}` : ''}
                ${source && companyName ? ' | ' : ''}
                ${companyName ? `Company: ${companyName}` : ''}
            </p>
            
            ${summary ? `<p class="text-gray-300 mb-4">"${summary}"</p>` : ''}
            
            <div class="mt-4">
                <a href="${url}" target="_blank" class="inline-flex items-center px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Read Full Article
                </a>
            </div>
        </div>
    `;
    
    return div;
}
</script>
{% endblock %}
