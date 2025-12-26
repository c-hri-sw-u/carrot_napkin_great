const CONFIG = {
    langMap: {
        'de': { name: 'german', package: 'mini-german-package-k3', label: 'German' },
        'ja': { name: 'japanese', package: 'mini-japanese-package-k3', label: 'Japanese' },
        'es': { name: 'spanish', package: 'mini-spanish-package-k3', label: 'Spanish' }
    },
    masteryThreshold: 5, // Updated to 5
    
    // Google Cloud TTS Configuration
    googleTTS: {
        apiKey: 'AIzaSyCMb2uaf7jC-8g29G9WV_nS2zvuXVuUf-I',
        baseUrl: 'https://texttospeech.googleapis.com/v1/text:synthesize',
        
        getVoiceName: (langCode) => {
            switch(langCode) {
                case 'en': return 'en-US-Wavenet-F';
                case 'zh': return 'cmn-CN-Wavenet-A';
                case 'es': return 'es-ES-Wavenet-F';
                case 'fr': return 'fr-FR-Wavenet-F';
                case 'de': return 'de-DE-Wavenet-G';
                case 'ja': return 'ja-JP-Wavenet-A';
                case 'ko': return 'ko-KR-Wavenet-A';
                case 'it': return 'it-IT-Wavenet-E';
                case 'pt': return 'pt-PT-Wavenet-E';
                case 'ru': return 'ru-RU-Wavenet-C';
                default: return 'en-US-Wavenet-F';
            }
        },
        
        getLanguageCode: (langCode) => {
             switch(langCode) {
                 case 'de': return 'de-DE';
                 case 'ja': return 'ja-JP';
                 case 'es': return 'es-ES';
                 default: return 'en-US';
             }
        },

        synthesize: async (text, langCode) => {
             const voiceName = CONFIG.googleTTS.getVoiceName(langCode);
             const languageCode = CONFIG.googleTTS.getLanguageCode(langCode);

             const body = {
                 input: { text: text },
                 voice: { languageCode: languageCode, name: voiceName },
                 audioConfig: { audioEncoding: 'MP3', speakingRate: 0.9, volumeGainDb: 10.0 }
             };

             try {
                 const response = await fetch(`${CONFIG.googleTTS.baseUrl}?key=${CONFIG.googleTTS.apiKey}`, {
                     method: 'POST',
                     headers: { 'Content-Type': 'application/json' },
                     body: JSON.stringify(body)
                 });
                 const data = await response.json();
                 if (data.audioContent) {
                    return data.audioContent;
                } else {
                    // Check for specific API disabled error
                    if (data.error && data.error.message && data.error.message.includes('blocked')) {
                        console.warn('Google TTS API not enabled/blocked. Will use system fallback.');
                    } else {
                        console.error('Google TTS API Error Details:', data);
                    }
                    return null;
                }
            } catch (error) {
                 console.error('Google TTS Network/Parse Error:', error);
                 return null;
             }
        }
    }
};

const app = {
    config: {
        ...CONFIG,
        characters: ['1', '2', '3']
    },

    state: {
        currentLang: null,
        character: '1', // Default character
        wordMap: new Map(), // TargetWord (normalized) -> { original: string, id: string, images: string[] }
        sequence: [], // Full Array of TargetWords (normalized) in order
        
        // Progress Tracking
        // level: 0..5. 
        // 0->1 (Learn 1), 1->2 (Learn 2), 2->3 (Test 1), 3->4 (Test 2), 4->5 (Test 3 -> Mastered)
        progressMap: new Map(), // TargetWord -> { level: 0, mastered: false }
        
        currentGroupIndex: 0,
        groupSize: 5, // Updated to 5
        
        currentIndex: 0, 
        activePool: [], 
        
        // Track current question state
        currentQuestionKey: null,
        currentQuestionFailed: false, // True if user made a mistake on this question attempt

        isAudioPlaying: false,
        currentAudioCache: null, // Cache for current question audio
        allKeys: [] 
    },

    config: CONFIG,

    warmUp: {
        items: [
            { name: "胡萝卜", image: "warm_up/萝卜.png", audio: "assets/audio/human/萝卜.MP3" },
            { name: "纸巾", image: "warm_up/纸巾.png", audio: "assets/audio/human/纸巾.MP3" },
            { name: "米老鼠", image: "warm_up/米老鼠.png", audio: "assets/audio/human/米老鼠.MP3" }
        ],
        targetIndex: null
    },

    init: () => {
        app.bindEvents();
        app.startWarmUp();
    },

    startWarmUp: () => {
        app.showScreen('warmup-screen');
        
        // Initialize character
        const charImg = document.getElementById('warmup-character-img');
        if (charImg) {
            charImg.src = `assets/img/1/idle.png?t=${Date.now()}`;
        }

        // Select random target
        const items = app.warmUp.items;
        app.warmUp.targetIndex = Math.floor(Math.random() * items.length);
        const target = items[app.warmUp.targetIndex];
        
        // Render options
        const container = document.getElementById('warmup-options-area');
        container.innerHTML = '';
        container.style.display = 'none'; // Hide initially

        const startBtnContainer = document.getElementById('warmup-start-container');
        startBtnContainer.style.display = 'block';

        const startBtn = document.getElementById('warmup-start-btn');
        // Remove old listeners by cloning
        const newStartBtn = startBtn.cloneNode(true);
        startBtn.parentNode.replaceChild(newStartBtn, startBtn);
        
        newStartBtn.addEventListener('click', () => {
            startBtnContainer.style.display = 'none';
            container.style.display = 'flex';
            app.playWarmUpAudio(target);
        });
        
        // Shuffle options for display
        const displayIndices = [0, 1, 2];
        app.shuffleArray(displayIndices);
        
        displayIndices.forEach(index => {
            const item = items[index];
            const el = document.createElement('div');
            el.className = 'option-card disabled'; // Start disabled
            
            // Add timestamp to prevent caching issues if any
            el.innerHTML = `<img src="${item.image}?t=${Date.now()}" alt="${item.name}">`;
            
            el.addEventListener('click', () => app.handleWarmUpSelection(index, el));
            container.appendChild(el);
        });
    },

    playWarmUpAudio: (target) => {
        const audio = new Audio(target.audio);
        audio.onended = () => {
            document.querySelectorAll('#warmup-options-area .option-card').forEach(el => el.classList.remove('disabled'));
        };
        audio.onerror = (e) => {
                console.error("Warmup audio error", e);
                // Enable anyway if audio fails
                document.querySelectorAll('#warmup-options-area .option-card').forEach(el => el.classList.remove('disabled'));
        };
        audio.play().catch(e => {
            console.error("Warmup audio play error", e);
            // Enable anyway if audio fails
            document.querySelectorAll('#warmup-options-area .option-card').forEach(el => el.classList.remove('disabled'));
        });
    },

    handleWarmUpSelection: (selectedIndex, el) => {
        if (el.classList.contains('disabled')) return;
        
        // Update character based on position (Left/Middle/Right)
        // Note: WarmUp options are shuffled but rendered in order in the DOM
        const parent = el.parentNode;
        const index = Array.from(parent.children).indexOf(el);
        let pos = 'neutral';
        if (index === 0) pos = 'left';
        else if (index === 1) pos = 'middle';
        else if (index === 2) pos = 'right';
        
        app.updateCharacter(pos);

        if (selectedIndex === app.warmUp.targetIndex) {
            // Correct
            el.style.borderColor = '#4CAF50';
            app.playEffect('posi', () => {
                setTimeout(() => {
                    app.showScreen('language-screen');
                }, 1000);
            });
        } else {
            // Incorrect
            el.style.borderColor = '#FF9800';
            app.playEffect('neg');
        }
    },

    bindEvents: () => {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const lang = e.target.getAttribute('data-lang');
                app.selectLanguage(lang);
            });
        });

        document.getElementById('endless-mode-btn').addEventListener('click', () => {
            app.startLoading();
        });

        // Settings Button Logic
        const modal = document.getElementById('settings-modal');
        const settingsBtn = document.getElementById('settings-btn');
        const closeBtn = document.querySelector('.close-modal');

        settingsBtn.addEventListener('click', () => {
            modal.classList.remove('hidden');
        });

        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });

        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });

        // Settings: Change Language
        document.querySelectorAll('.settings-lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const lang = e.target.getAttribute('data-lang');
                if (confirm(`Switch language to ${lang}? Current progress will be lost.`)) {
                    modal.classList.add('hidden');
                    app.selectLanguage(lang);
                    app.startLoading();
                }
            });
        });

        // Settings: Restart Mode
        document.getElementById('settings-restart-btn').addEventListener('click', () => {
             if (confirm("Restart Endless Mode? Current progress will be lost.")) {
                 modal.classList.add('hidden');
                 app.startLoading(); // Reloads data and restarts
             }
        });

        // Settings: Populate Character Selection
        const charContainer = document.getElementById('settings-char-container');
        charContainer.innerHTML = '';
        charContainer.style.display = 'flex';
        charContainer.style.flexDirection = 'row';
        charContainer.style.flexWrap = 'nowrap';
        charContainer.style.overflowX = 'auto';
        charContainer.style.gap = '15px';
        charContainer.style.justifyContent = 'flex-start';
        charContainer.style.padding = '10px';
        charContainer.style.width = '100%';
        charContainer.style.boxSizing = 'border-box';

        const characters = (typeof CHARACTER_MANIFEST !== 'undefined') ? CHARACTER_MANIFEST : ['1'];

        characters.forEach(charId => {
            const btn = document.createElement('div');
            btn.style.flexShrink = '0'; // Prevent shrinking
            btn.style.cursor = 'pointer';
            btn.style.border = app.state.character === charId ? '3px solid #4CAF50' : '3px solid transparent';
            btn.style.borderRadius = '8px';
            btn.style.overflow = 'hidden';
            btn.style.width = '80px';
            btn.style.height = '80px';
            btn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';

            const img = document.createElement('img');
            img.src = `assets/img/${charId}/idle.png`;
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            
            btn.appendChild(img);

            btn.addEventListener('click', () => {
                app.state.character = charId;
                
                // Update UI selection
                Array.from(charContainer.children).forEach(c => c.style.border = '3px solid transparent');
                btn.style.border = '3px solid #4CAF50';
                
                app.updateCharacter('idle'); // Update immediately if in game
            });
            charContainer.appendChild(btn);
        });

        // Global click listener for Character "Other" state
        window.addEventListener('click', (e) => {
            // If click is NOT on an option card, show _.png
            // But we must ensure we are in the game screen
            if (document.getElementById('game-screen').classList.contains('hidden')) return;
            
            // Replay button listener (delegated or added separately, but let's just ignore clicks on it for "Other" char)
            if (e.target.closest('#replay-audio-btn')) return;
            // Delete button listener
            if (e.target.closest('#delete-word-btn')) return;

            // If clicking on settings or modal, ignore? 
            // User said "click screen other place".  
            // Let's assume if it's NOT an option card, switch to _.
            // But wait, clicking "Next" (if there was one) or clicking Settings shouldn't trigger this necessarily?
            // Actually, clicking settings is "other place".
            // Let's just check if it's NOT an option card.
            
            if (!e.target.closest('.option-card')) {
                 // Only switch if we are NOT currently processing a correct answer animation?
                 // User didn't specify. Just "click other place -> _.png".
                 // But if we are in "idle" state, it switches to "_".
                 // If we just clicked an option, we are in "left/right/middle".
                 // If we click background, we go to "_".
                 app.updateCharacter('neutral');
            }
        });

        // Replay Audio Button
        const replayBtn = document.getElementById('replay-audio-btn');
        if (replayBtn) {
            replayBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent "Other" character logic
                if (app.state.currentQuestionKey) {
                    const targetData = app.state.wordMap.get(app.state.currentQuestionKey);
                    if (targetData) {
                        // Disable button temporarily to prevent spam?
                        replayBtn.style.opacity = '0.5';
                        replayBtn.style.pointerEvents = 'none';
                        app.playAudio(targetData.original, () => {
                            replayBtn.style.opacity = '1';
                            replayBtn.style.pointerEvents = 'auto';
                        });
                    }
                }
            });
        }

        // Delete Word Button
        const deleteBtn = document.getElementById('delete-word-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent "Other" character logic
                if (app.state.currentQuestionKey) {
                    if (confirm("Remove this word from the list?")) {
                        app.removeCurrentWord();
                    }
                }
            });
        }
    },

    removeCurrentWord: () => {
        const key = app.state.currentQuestionKey;
        if (!key) return;

        // Remove from wordMap
        app.state.wordMap.delete(key);
        
        // Remove from sequence
        const seqIndex = app.state.sequence.indexOf(key);
        if (seqIndex > -1) {
            app.state.sequence.splice(seqIndex, 1);
        }

        // Remove from allKeys
        const allKeyIndex = app.state.allKeys.indexOf(key);
        if (allKeyIndex > -1) {
            app.state.allKeys.splice(allKeyIndex, 1);
        }
        
        // Remove from progressMap
        app.state.progressMap.delete(key);

        console.log(`Removed word: ${key}`);
        
        // Track deleted count for progress bar
        app.state.deletedCount = (app.state.deletedCount || 0) + 1;

        // Update active pool and move to next question
        // If current group becomes empty, updateActivePool logic in nextQuestion/updateActivePool will handle it?
        // Let's force updateActivePool to re-evaluate
        
        // If we just removed the last word of the group, we might need to advance group or finish
        // But app.updateActivePool() is called in app.nextQuestion()
        
        // Update progress bar because total count changed
        app.updateProgressBar();

        // Just call nextQuestion immediately
        app.nextQuestion();
    },

    updateCharacter: (type) => {
        const charId = app.state.character;
        
        // Update Game Character
        const imgEl = document.getElementById('character-img');
        if (imgEl) {
            imgEl.src = `assets/img/${charId}/${type}.png?t=${Date.now()}`;
        }
        
        // Update Warm Up Character (if visible or exists)
        const warmupImgEl = document.getElementById('warmup-character-img');
        if (warmupImgEl) {
            warmupImgEl.src = `assets/img/${charId}/${type}.png?t=${Date.now()}`;
        }
        
        // Clear any existing idle timer
        if (app.state.idleTimer) {
            clearTimeout(app.state.idleTimer);
            app.state.idleTimer = null;
        }

        // If not idle, set timer to revert to idle after 2 seconds
        if (type !== 'idle') {
            app.state.idleTimer = setTimeout(() => {
                app.updateCharacter('idle');
            }, 2000);
        }
    },

    selectLanguage: (lang) => {
        app.state.currentLang = lang;
        app.showScreen('mode-screen');
    },

    showScreen: (screenId) => {
        document.querySelectorAll('.screen').forEach(el => el.classList.add('hidden'));
        document.getElementById(screenId).classList.remove('hidden');
    },

    startLoading: async () => {
        app.showScreen('loading-screen');
        const statusEl = document.getElementById('loading-status');
        
        try {
            await app.loadData(statusEl);
            app.startGame();
        } catch (error) {
            console.error(error);
            statusEl.innerText = 'Error loading data: ' + error.message;
        }
    },

    loadData: async (statusEl) => {
        const lang = app.state.currentLang;
        const langConfig = app.config.langMap[lang];
        app.state.wordMap.clear();
        app.state.progressMap.clear();
        
        statusEl.innerText = 'Loading word sequence...';
        
        const scaleFile = `${langConfig.package}/index.csv`;
        const response = await fetch(scaleFile);
        if (!response.ok) throw new Error(`Failed to load ${scaleFile}`);
        const text = await response.text();
        
        app.parseScaleCSV(text, langConfig.package);
        
        app.state.allKeys = Array.from(app.state.wordMap.keys());
        console.log(`Loaded ${app.state.allKeys.length} words with images.`);

        if (app.state.allKeys.length === 0) {
            throw new Error("No valid words found in package (checking manifest).");
        }
        
        app.state.sequence.forEach(key => {
            app.state.progressMap.set(key, { level: 0, mastered: false, seenCount: 0 });
        });

        app.shuffleArray(app.state.sequence);
    },

    parseScaleCSV: (text, packageName) => {
        const lines = text.split('\n');
        const sequence = [];

        if (typeof PACKAGE_MANIFEST === 'undefined' || !PACKAGE_MANIFEST[packageName]) {
            console.error("Manifest not found for " + packageName);
            return;
        }
        
        const packageImages = PACKAGE_MANIFEST[packageName];

        for (let i = 1; i < lines.length; i++) { 
            const line = lines[i].trim();
            if (!line) continue;
            
            const parts = line.split(',');
            if (parts.length < 2) continue;
            
            const word = parts[parts.length - 1].trim();
            const id = parts[parts.length - 2].trim();
            
            if (packageImages[id] && packageImages[id].length > 0) {
                const normalized = app.normalizeText(word);
                app.state.wordMap.set(normalized, {
                    original: word,
                    id: id,
                    images: packageImages[id].map(img => `${packageName}/${id}/${img}`)
                });
                sequence.push(normalized);
            }
        }
        
        app.state.sequence = sequence;
    },

    normalizeText: (text) => {
        let str = text.toLowerCase();
        if (app.state.currentLang === 'de') {
            str = str.replace(/^(der|die|das)\s+/, '');
        }
        if (app.state.currentLang === 'es') {
            str = str.replace(/^(el|la|los|las)\s+/, '');
        }
        return str.trim();
    },

    shuffleArray: (array) => {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    },

    startGame: () => {
        app.state.currentGroupIndex = 0;
        app.updateActivePool();
        app.updateProgressBar();
        app.showScreen('game-screen');
        app.nextQuestion();
    },

    updateActivePool: () => {
        const start = app.state.currentGroupIndex * app.state.groupSize;
        const end = start + app.state.groupSize;
        const groupKeys = app.state.sequence.slice(start, end);
        
        app.state.activePool = groupKeys.filter(key => {
            const p = app.state.progressMap.get(key);
            return p && !p.mastered;
        });

        if (app.state.activePool.length === 0 && groupKeys.length > 0) {
             if (end < app.state.sequence.length) {
                 app.state.currentGroupIndex++;
                 app.updateActivePool(); 
             } else {
                 alert("Congratulations! You have mastered all words!");
                 location.reload(); 
             }
        }
    },

    nextQuestion: () => {
        app.updateCharacter('idle'); // Reset character
        app.updateActivePool();
        if (app.state.activePool.length === 0) return; 

        // Clear audio cache for new question
        app.state.currentAudioCache = null;

        // Weighted selection? Or simple random?
        // Simple random is fine for small groups of 5.
        const poolIndex = Math.floor(Math.random() * app.state.activePool.length);
        const targetKey = app.state.activePool[poolIndex];
        
        app.state.currentQuestionKey = targetKey;
        app.state.currentQuestionFailed = false; // Reset failure flag for new question

        const targetData = app.state.wordMap.get(targetKey);
        const progress = app.state.progressMap.get(targetKey);
        
        // Increment seen count
        progress.seenCount = (progress.seenCount || 0) + 1;
        
        // Update Level Indicator
        app.updateLevelIndicator(progress.level, progress.seenCount);

        document.getElementById('current-word').innerText = targetData.original;
        document.getElementById('message-area').innerText = '';

        const options = app.generateOptions(targetKey);
        const optionsArea = document.getElementById('options-area');
        optionsArea.innerHTML = '';
        
        options.forEach(opt => {
            const el = document.createElement('div');
            el.className = 'option-card disabled';
            
            // Select a random image from the available images for this word
            // Add timestamp to prevent browser caching
            const imgIndex = Math.floor(Math.random() * opt.images.length);
            const randomImg = opt.images[imgIndex];
            
            // Debug log to verify randomness
            console.log(`Word: ${opt.original} (ID: ${opt.id}) - Selected Image: ${randomImg} (${imgIndex + 1}/${opt.images.length})`);
            
            el.innerHTML = `<img src="${randomImg}?t=${Date.now()}" alt="Option">`;
            el.dataset.key = opt.key;
            el.addEventListener('click', () => app.handleSelection(el, targetKey));
            optionsArea.appendChild(el);
        });

        app.playAudio(targetData.original, () => {
            document.querySelectorAll('.option-card').forEach(el => el.classList.remove('disabled'));
        });
    },
    
    updateLevelIndicator: (level, seenCount) => {
        const indicator = document.getElementById('word-level-indicator');
        // Logic:
        // Level 0, 1 -> Learning
        // Level 2 -> Test 1/3
        // Level 3 -> Test 2/3
        // Level 4 -> Test 3/3
        
        let statusText = "";
        if (level < 2) {
            statusText = `Learning`; 
        } else {
            const testStage = level - 1; // 2->1, 3->2, 4->3
            statusText = `Test: ${testStage}/3`;
        }
        
        indicator.innerHTML = `<span>${statusText}</span> <span style="margin-left: 15px; color: #666;">Seen: ${seenCount}</span>`;
    },

    generateOptions: (correctKey) => {
        const correctData = app.state.wordMap.get(correctKey);
        const options = [{ key: correctKey, ...correctData }];
        const otherKeys = app.state.allKeys.filter(k => k !== correctKey);
        
        while (options.length < 3 && otherKeys.length > 0) {
            const randomKey = otherKeys[Math.floor(Math.random() * otherKeys.length)];
            if (!options.find(o => o.key === randomKey)) {
                options.push({ key: randomKey, ...app.state.wordMap.get(randomKey) });
            }
        }
        app.shuffleArray(options);
        return options;
    },

    playAudio: async (text, onEnd) => {
        // Check cache first
        if (app.state.currentAudioCache) {
            const audio = new Audio(app.state.currentAudioCache);
            audio.onended = () => { if (onEnd) onEnd(); };
            audio.onerror = (e) => { 
                console.error("Cached audio playback error", e); 
                if (onEnd) onEnd(); 
            };
            audio.play().catch(e => {
                console.error("Cached audio play error", e);
                if (onEnd) onEnd();
            });
            return;
        }

        // Try Google TTS first
        try {
            const audioContent = await app.config.googleTTS.synthesize(text, app.state.currentLang);
            if (audioContent) {
                const dataUrl = "data:audio/mp3;base64," + audioContent;
                app.state.currentAudioCache = dataUrl; // Cache it
                
                const audio = new Audio(dataUrl);
                audio.onended = () => { if (onEnd) onEnd(); };
                audio.onerror = (e) => { 
                    console.error("Audio playback error", e); 
                    if (onEnd) onEnd(); 
                };
                audio.play().catch(e => {
                    console.error("Play error", e);
                    if (onEnd) onEnd();
                });
                return;
            }
        } catch (e) {
            console.error("Google TTS failed, falling back to Web Speech API", e);
        }

        // Fallback to Web Speech API
        console.log("Using Web Speech API fallback.");
        if (!window.speechSynthesis) {
            console.warn("Speech Synthesis not supported");
            if (onEnd) onEnd();
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.volume = 1.0; // Max volume
        utterance.lang = app.getVoiceLang(app.state.currentLang);
        utterance.onend = () => { if (onEnd) onEnd(); };
        utterance.onerror = (e) => { console.error("Audio error", e); if (onEnd) onEnd(); };
        window.speechSynthesis.speak(utterance);
    },

    getVoiceLang: (langCode) => {
        switch(langCode) {
            case 'de': return 'de-DE';
            case 'ja': return 'ja-JP';
            case 'es': return 'es-ES';
            default: return 'en-US';
        }
    },

    playEffect: (type, onEnd) => {
        if (typeof AUDIO_MANIFEST === 'undefined' || !AUDIO_MANIFEST[type] || AUDIO_MANIFEST[type].length === 0) {
            if (onEnd) onEnd();
            return;
        }
        
        const files = AUDIO_MANIFEST[type];
        const randomFile = files[Math.floor(Math.random() * files.length)];
        let folder = '';
        if (type === 'posi') folder = 'human/posi';
        else if (type === 'neg') folder = 'human/neg';
        else if (type === 'cat') folder = 'cat';
        
        // Cache bust audio
        const audio = new Audio(`assets/audio/${folder}/${randomFile}?t=${Date.now()}`);
        audio.onended = () => { if (onEnd) onEnd(); };
        audio.onerror = (e) => { 
            console.error("Effect audio error", e);
            if (onEnd) onEnd(); 
        };
        audio.play().catch(e => {
            console.error("Effect play error", e);
            if (onEnd) onEnd();
        });
    },

    playTreatAnimation: (startEl) => {
        const startRect = startEl.getBoundingClientRect();
        const charEl = document.getElementById('character-img');
        if (!charEl) return;
        
        const endRect = charEl.getBoundingClientRect();
        
        // Create Treat Element
        const treat = document.createElement('div');
        treat.style.position = 'fixed';
        treat.style.width = '60px';
        treat.style.height = '60px';
        treat.style.zIndex = '10000';
        treat.style.pointerEvents = 'none';
        treat.style.transition = 'all 1s cubic-bezier(0.68, -0.55, 0.265, 1.55)'; // Bouncy effect
        
        // Start Position (Centered on option)
        const startLeft = startRect.left + (startRect.width / 2) - 30;
        const startTop = startRect.top + (startRect.height / 2) - 30;
        
        treat.style.left = startLeft + 'px';
        treat.style.top = startTop + 'px';
        
        // SVG Content - Simple Fish Biscuit
        treat.innerHTML = `
            <svg viewBox="0 0 100 60" width="100%" height="100%">
                <!-- Fish body -->
                <ellipse cx="60" cy="30" rx="30" ry="20" fill="#FFA726" stroke="#E65100" stroke-width="2" />
                <!-- Tail -->
                <path d="M35,30 L10,10 L10,50 Z" fill="#FFA726" stroke="#E65100" stroke-width="2" />
                <!-- Eye -->
                <circle cx="75" cy="25" r="2" fill="#3E2723" />
                <!-- Mouth -->
                <path d="M85,30 Q88,30 90,32" stroke="#3E2723" stroke-width="2" fill="none" />
            </svg>
        `;
        
        document.body.appendChild(treat);
        
        // Force Reflow
        void treat.offsetWidth;
        
        // End Position (Centered on character)
        // Aim for the mouth area (slightly lower than center for most chars)
        const endLeft = endRect.left + (endRect.width / 2) - 30;
        const endTop = endRect.top + (endRect.height / 2) - 10; 
        
        treat.style.left = endLeft + 'px';
        treat.style.top = endTop + 'px';
        treat.style.transform = 'scale(1.2) rotate(360deg)'; // Scaled up at end
        treat.style.opacity = '0'; // Fade out
        
        // Cleanup
        setTimeout(() => {
            if (treat.parentNode) {
                treat.parentNode.removeChild(treat);
            }
        }, 1000);
    },

    updateTreatCount: () => {
        app.state.treatCount = (app.state.treatCount || 0) + 1;
        document.getElementById('treat-count-value').innerText = app.state.treatCount;
    },

    handleSelection: (el, correctKey) => {
        if (el.classList.contains('checked')) return;
        
        // Update character based on position (Left/Middle/Right)
        const parent = el.parentNode;
        const index = Array.from(parent.children).indexOf(el);
        let pos = '_';
        if (index === 0) pos = 'left';
        else if (index === 1) pos = 'middle';
        else if (index === 2) pos = 'right';
        
        app.updateCharacter(pos);

        const selectedKey = el.dataset.key;
        const isCorrect = selectedKey === correctKey;
        const progress = app.state.progressMap.get(correctKey);
        
        el.classList.add('checked');
        
        if (isCorrect) {
            el.classList.add('correct');
            document.getElementById('message-area').innerText = '蒸蚌!';
            document.getElementById('message-area').style.color = 'green';
            
            // Logic:
            // Phase 1 (Level 0, 1): Always advance level on correct (even if failed before in this turn)
            // Phase 2 (Level >= 2): Only advance if NOT failed in this turn.
            
            let shouldAdvance = false;
            
            if (progress.level < 2) {
                // Phase 1: Always advance eventually
                shouldAdvance = true;
            } else {
                // Phase 2: Only advance if perfect on first try
                if (!app.state.currentQuestionFailed) {
                    shouldAdvance = true;
                } else {
                    // Stay at current level
                    // console.log("Correct but failed first try, no advance.");
                }
            }
            
            if (shouldAdvance) {
                progress.level++;
                if (progress.level >= app.config.masteryThreshold) {
                    progress.mastered = true;
                }
            }

            app.updateProgressBar();
            document.querySelectorAll('.option-card').forEach(c => c.classList.add('disabled'));
            
            // Trigger Treat Animation
            app.playTreatAnimation(el);
            app.updateTreatCount();

            // Play Posi effect, then Next Question
            app.playEffect('posi', () => {
                // 30% chance for Cat sound when entering next question
                if (Math.random() < 0.3) {
                    app.playEffect('cat');
                }
                app.nextQuestion();
            });
            
        } else {
            el.classList.add('wrong');
            document.getElementById('message-area').innerText = 'No. Try Again!';
            document.getElementById('message-area').style.color = 'orange';
            
            // Mark as failed for this question attempt
            app.state.currentQuestionFailed = true;
            
            // Note: We do NOT reset level to 0 anymore based on new requirements.
            // We just ensure they don't advance level if they are in Phase 2.
            
            app.playEffect('neg');
        }
    },
    
    updateProgressBar: () => {
        let masteredCount = 0;
        // Count mastered words, AND deleted words should also be considered "done" or just removed from denominator?
        // User said: "After deleting, it should be reflected on the progress bar, completion + 1"
        // This implies deleting a word counts as completing it? Or just that the percentage goes up?
        // If I delete a word, it's gone from progressMap and sequence.
        // So `total` (sequence.length) decreases.
        // If I have 10 words, 0 mastered. 0/10 = 0%.
        // Delete 1. 9 words, 0 mastered. 0/9 = 0%.
        // User wants "completion + 1". 
        // Maybe they want the deleted word to be treated as "Mastered" (numerator + 1) but kept in total?
        // OR they want the denominator to stay same, but numerator to increase?
        
        // "Delete" usually means "I don't need to learn this". So it is effectively mastered.
        // But we removed it from `sequence` and `progressMap`.
        // To implement "completion + 1", we need to track how many were deleted.
        
        // Let's count how many words were originally loaded vs how many are left.
        // But we don't store original count.
        
        // Wait, if I simply remove it from sequence, the total decreases.
        // 5/10 (50%) -> delete 1 unmastered -> 5/9 (55%). Progress goes up.
        // 5/10 (50%) -> delete 1 mastered -> 4/9 (44%). Progress goes down? That's bad.
        
        // If the user deletes a word, we probably shouldn't remove it from the total count if we want to show "completion".
        // Instead, let's mark it as "skipped/deleted" in progressMap and treat it as mastered for the progress bar calculation?
        // But `removeCurrentWord` implementation DELETED it from the map.
        
        // Let's modify `updateProgressBar` to use `app.state.allKeys.length` vs `app.state.sequence.length`?
        // `sequence` was spliced. `allKeys` was spliced.
        
        // Let's assume the user means "The progress percentage should reflect that I have one less thing to do".
        // My current implementation (removing from total) DOES increase the percentage if the deleted word was unmastered.
        // Example: 0/10 (0%). Delete 1. 0/9 (0%). Wait, that's still 0%.
        // If user wants "completion + 1", maybe they mean "Treat it as if I finished it".
        // 0/10 -> 1/10 (10%).
        
        // To support "completion + 1", I should NOT delete it from `allKeys` or `sequence` completely?
        // Or I should track `deletedCount`.
        
        // Let's try tracking `deletedCount` in state.
        const deletedCount = app.state.deletedCount || 0;
        
        let masteredCountFromMap = 0;
        app.state.progressMap.forEach(p => {
            if (p.mastered) masteredCountFromMap++;
        });
        
        // Effective Mastered = Mastered + Deleted
        const effectiveMastered = masteredCountFromMap + deletedCount;
        
        // Effective Total = Current Sequence Length + Deleted
        const effectiveTotal = app.state.sequence.length + deletedCount;
        
        // Wait, `sequence` was spliced.
        // If I started with 10. sequence.length is 10.
        // I delete 1. sequence.length is 9. deletedCount is 1.
        // Effective Total = 9 + 1 = 10. Correct.
        // Effective Mastered = 0 + 1 = 1.
        // Percentage = 1/10 = 10%.
        
        // This seems to match "completion + 1".
        
        const total = effectiveTotal;
        const percentage = total > 0 ? Math.round((effectiveMastered / total) * 100) : 0;
        
        document.getElementById('progress-bar-fill').style.width = `${percentage}%`;
        document.getElementById('progress-text').innerText = `Progress: ${percentage}% (${effectiveMastered}/${total})`;
    }
};

app.init();
