# Lab 7 - Reflection

**Q1. What did you learn about fuzz testing?**

Fuzzing flips how I usually test. Instead of me hand-picking a few inputs I think are tricky, Hypothesis generates hundreds of random ones and shrinks each failure down to the smallest input that still breaks the code. Every bug in this program was found with inputs I would never have typed myself, like an empty string or a single "0".

**Q2. Which bugs found by fuzzing were most surprising?**

The `delivery_zone("")` crash surprised me the most. `pincode[0]` looks harmless until the string is empty, and the empty string is literally the first thing the fuzzer tries. The silent bugs were worse than the crashes though: `promo_percent("OFF250")` happily returns 250, and `delivery_zone("5")` returns "South" for a 1 digit pincode. Those would never show up as errors, just wrong data going downstream.

**Q3. How is fuzzing different from the coverage testing in Lab 6?**

Coverage tells you which lines your tests executed, nothing more. In Lab 6 I could hit 100% coverage with only nice, valid inputs. Fuzzing does not care about my assumptions: it tries None, empty strings, unicode, huge inputs, and finds the edges where the code's assumptions break. High coverage plus fuzzing together is much stronger than either alone.

**Q4. How will you use fuzzing in future projects?**

Any function that takes outside input (form fields, API parameters, file uploads) deserves a `no_crash` property test. It costs about five lines with Hypothesis and it forces you to decide upfront: reject bad input cleanly, or handle it. I will also stop trusting "it works on the happy path" as done, because this lab showed how many ways the unhappy path can break.
