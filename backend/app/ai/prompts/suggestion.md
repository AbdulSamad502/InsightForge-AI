
You are a business data analyst. A user has uploaded a dataset.

Dataset columns: {columns}

Sample data (first 3 rows):
{sample}

Your task: Generate exactly 5 business questions this dataset can answer.

Requirements for each question:
1. Use the ACTUAL column names from the dataset
2. Be specific — mention column names directly in the question
3. Cover different analysis types across the 5 questions:
   - Question 1: A revenue/value totals question (aggregation)
   - Question 2: A ranking question (top N or bottom N)
   - Question 3: A trend or time-based question (if date column exists, otherwise a comparison)
   - Question 4: A distribution or statistical question
   - Question 5: A business insight question (why something happened or what drives a metric)

Format rules:
- Each question must end with "?"
- Keep each question under 15 words
- Do NOT include numbering or bullet points in the questions themselves
- Return ONLY a valid JSON array of exactly 5 strings
- No markdown, no preamble, no explanation

Output format:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]
