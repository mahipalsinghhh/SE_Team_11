# Lab 5 - Reflection

**Q1. What did you learn about static code analysis?**

Static analysis lets you catch bugs, security holes and style problems without even running the code. Before this lab I mostly relied on running the program and checking the output, but this program actually "worked" while still having an SQL injection risk and a shared mutable default list. That showed me that working output does not mean correct or safe code.

**Q2. Which issues found by the tools were most surprising or valuable?**

The mutable default argument (`log=[]`) was the most surprising one. Every call to `addStation` was appending to the same list object, which is a classic Python trap I would not have noticed on my own. The `hasBikes` crash was also valuable: the code compared `row[0] == None` but the real problem was that `fetchone()` returns None for a missing station, so the function would blow up before the comparison even ran. Bandit flagging the SQL string concatenation was useful too, since that pattern is genuinely exploitable.

**Q3. How do Pylint, Bandit and Flake8 differ in what they catch?**

They look at different layers. Bandit is purely about security: SQL injection, weak randomness, swallowed exceptions. Pylint is the strict reviewer for logic and design: unused variables, inconsistent returns, wrong None comparisons, naming. Flake8 is mostly about PEP 8 formatting like line length and whitespace, though its pyflakes part also caught the unused variable. Running only one of them would have left real issues in place.

**Q4. How will you apply static analysis in your future projects?**

I want to wire these tools into my projects early instead of running them once at the end. Even adding pylint and flake8 to a pre-commit step or CI would catch most of what I fixed here automatically. I will also write SQL with parameterized queries from the start, since that is easier than retrofitting it after Bandit complains.
