document.querySelectorAll('[data-quiz]').forEach((quiz) => {
  const feedback = quiz.querySelector('[data-feedback]');

  quiz.querySelectorAll('button[data-answer]').forEach((button) => {
    button.addEventListener('click', () => {
      const correct = button.dataset.answer === 'right';
      feedback.className = `feedback ${correct ? 'correct' : 'wrong'}`;
      feedback.textContent = correct
        ? quiz.dataset.correct
        : quiz.dataset.wrong;
    });
  });
});
