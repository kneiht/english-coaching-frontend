
document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const checkAnswersBtn = document.getElementById('check-answers-btn');
    const showScriptBtn = document.getElementById('show-script-btn');
    const showAnswersBtn = document.getElementById('show-answers-btn');
    const allExercisesData = window.allExercisesData || [];
    const scriptPassword = window.scriptPassword;
    const audioSpeed = window.audioSpeed || 1.0;

    // Set audio speed for all audio elements
    document.querySelectorAll('audio').forEach(audio => {
        audio.playbackRate = audioSpeed;
    });

    // Tab switching logic
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetType = tab.dataset.tab;

            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            tabContents.forEach(content => {
                if (content.id === targetType) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
            // Hide all results/scripts when switching tabs
            document.querySelectorAll('.results-container, .script-container').forEach(el => el.style.display = 'none');
            
            const activeExercise = allExercisesData.find(ex => ex.type === targetType);
            if(showScriptBtn) {
               showScriptBtn.style.display = activeExercise && activeExercise.script ? 'inline-block' : 'none';
            }
            if(showAnswersBtn) {
               showAnswersBtn.style.display = activeExercise ? 'inline-block' : 'none';
            }
        });
    });

    // Function to calculate similarity for dictation
    function calculateSimilarity(s1, s2) {
        let longer = s1;
        let shorter = s2;
        if (s1.length < s2.length) {
            longer = s2;
            shorter = s1;
        }
        const longerLength = longer.length;
        if (longerLength === 0) {
            return 1.0;
        }
        const distance = (longerLength - editDistance(longer, shorter)) / parseFloat(longerLength);
        return distance * 100;
    }

    function editDistance(s1, s2) {
        s1 = s1.toLowerCase();
        s2 = s2.toLowerCase();
        const costs = [];
        for (let i = 0; i <= s1.length; i++) {
            let lastValue = i;
            for (let j = 0; j <= s2.length; j++) {
                if (i === 0) {
                    costs[j] = j;
                } else {
                    if (j > 0) {
                        let newValue = costs[j - 1];
                        if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
                            newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                        }
                        costs[j - 1] = lastValue;
                        lastValue = newValue;
                    }
                }
            }
            if (i > 0) costs[s2.length] = lastValue;
        }
        return costs[s2.length];
    }
    
    // Check answers logic
    if (checkAnswersBtn) {
        checkAnswersBtn.addEventListener('click', () => {
            const activeTab = document.querySelector('.tab-btn.active');
            if (!activeTab) return;
            
            const exerciseType = activeTab.dataset.tab;
            const exerciseData = allExercisesData.find(ex => ex.type === exerciseType);
            if (!exerciseData) return;

            const prefix = window.EXERCISE_PREFIX[exerciseType];
            let totalCorrect = 0;
            const totalQuestions = exerciseData.questions.length;
            const dictationScores = [];

            exerciseData.questions.forEach((q) => {
                const questionElement = document.getElementById(`${prefix}_q-${q.id}`);
                if (!questionElement) return;

                const feedbackElement = questionElement.querySelector('.feedback');
                if (feedbackElement) feedbackElement.innerHTML = '';
                
                let isCorrect = false;

                switch (exerciseType) {
                    case 'multiple-choice': {
                        const selected = questionElement.querySelector('input:checked');
                        if (selected) isCorrect = selected.value === q.correctAnswer;
                        break;
                    }
                    case 'fill-in-the-blank': {
                        const input = questionElement.querySelector('input[type="text"]');
                        if (input) {
                            const cleanUserAnswer = input.value.trim().toLowerCase().replace(/[^a-zA-Z0-9 ]/g, '');
                            const cleanCorrectAnswer = q.correctAnswer.trim().toLowerCase().replace(/[^a-zA-Z0-9 ]/g, '');
                            isCorrect = cleanUserAnswer === cleanCorrectAnswer;
                        }
                        break;
                    }
                    case 'dictation': {
                        const correctAnswerText = q.audioScript;
                        const textarea = questionElement.querySelector('textarea');
                        if (textarea) {
                            const userAnswer = textarea.value;
                            const score = calculateSimilarity(userAnswer, correctAnswerText);
                            dictationScores.push({ id: q.id, score: score.toFixed(0) });
                            isCorrect = score > 80;
                             if (feedbackElement) {
                                feedbackElement.innerHTML = `<span class="text-gray-300">Accuracy: </span><span class="font-bold text-white">${score.toFixed(0)}%</span>`;
                            }
                        }
                        break;
                    }
                    case 'true-false': {
                        const selected = questionElement.querySelector('input:checked');
                        if (selected) isCorrect = selected.value === String(q.correctAnswer);
                        break;
                    }
                }

                if (isCorrect) {
                    if (exerciseType !== 'dictation') totalCorrect++;
                    questionElement.classList.add('correct');
                    questionElement.classList.remove('incorrect');
                } else {
                    questionElement.classList.add('incorrect');
                    questionElement.classList.remove('correct');
                }
                
                if (feedbackElement && exerciseType !== 'dictation') {
                    feedbackElement.textContent = isCorrect ? 'Correct!' : 'Incorrect.';
                    feedbackElement.style.color = isCorrect ? '#34d399' : '#f87171';
                }
            });
            
            const resultsContainer = document.querySelector(`#${exerciseType} .results-container`);
            if (resultsContainer) {
                if (exerciseType === 'dictation') {
                     const averageScore = dictationScores.length > 0 ? dictationScores.reduce((acc, s) => acc + parseFloat(s.score), 0) / dictationScores.length : 0;
                     resultsContainer.innerHTML = `<h3>Overall Report</h3><p class="text-2xl mt-2">Average Accuracy: <span class="font-bold">${averageScore.toFixed(0)}%</span></p>`;
                } else {
                    resultsContainer.innerHTML = `<h3>Results</h3><p class="text-2xl mt-2">You got <span class="font-bold">${totalCorrect}</span> out of <span class="font-bold">${totalQuestions}</span> correct!</p>`;
                }
                resultsContainer.style.display = 'block';
            }
        });
    }

    if (showAnswersBtn) {
        showAnswersBtn.addEventListener('click', () => {
            const activeTab = document.querySelector('.tab-btn.active');
            if (!activeTab) return;
            
            const exerciseType = activeTab.dataset.tab;
            const exerciseData = allExercisesData.find(ex => ex.type === exerciseType);
            if (!exerciseData) return;

            const password = prompt('Please enter the password to view the answers:');
            if (password === scriptPassword) {
                exerciseData.questions.forEach(q => {
                    const prefix = window.EXERCISE_PREFIX[exerciseType];
                    const questionElement = document.getElementById(`${prefix}_q-${q.id}`);
                    if (!questionElement) return;

                    const feedbackElement = questionElement.querySelector('.feedback');
                    if (!feedbackElement) return;
                    
                    if (feedbackElement.innerHTML.includes('Correct answer:')) return;

                    let correctAnswerText = '';
                    switch (exerciseType) {
                        case 'multiple-choice':
                        case 'fill-in-the-blank':
                            correctAnswerText = q.correctAnswer;
                            break;
                        case 'true-false':
                            correctAnswerText = String(q.correctAnswer);
                            break;
                        case 'dictation':
                            correctAnswerText = q.audioScript;
                            break;
                    }

                    feedbackElement.innerHTML += ` <br><span class="font-semibold text-gray-300">Correct answer: </span><span class="text-cyan-300 italic">"${correctAnswerText}"</span>`;
                });
            } else if (password !== null) {
                alert('Incorrect password.');
            }
        });
    }

    if (showScriptBtn) {
        showScriptBtn.addEventListener('click', () => {
             const activeTab = document.querySelector('.tab-btn.active');
            if (!activeTab) return;
            
            const exerciseType = activeTab.dataset.tab;
            const exerciseData = allExercisesData.find(ex => ex.type === exerciseType);
            
            if (!exerciseData || !exerciseData.script) {
                alert('No script available for this exercise.');
                return;
            };

            const password = prompt('Please enter the password to view the script:');
            if (password === scriptPassword) {
                const scriptContainer = document.querySelector(`#${exerciseType} .script-container`);
                const scriptContent = document.querySelector(`#${exerciseType} .script-content`);
                if (scriptContent) scriptContent.textContent = exerciseData.script;
                if (scriptContainer) scriptContainer.style.display = 'block';
            } else if (password !== null) {
                alert('Incorrect password.');
            }
        });
    }

    // Trigger click on the first tab to initialize view
    if (tabs.length > 0) {
        tabs[0].click();
    }
});
