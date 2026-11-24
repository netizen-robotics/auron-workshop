# Agentic Coding

[Workshop topic index](../README.md#topics)

Use OpenCode Desktop on the laptop and run the exercises from the checkout root in the Dev Container.

## 02 · Agentic Coding with OpenCode Desktop

OpenCode can inspect the project and edit its files. Review the plan and changes, then run the tests to verify the result.

1. Run the previews and tests in the VS Code Dev Container. Predict the correct signed speeds given a limit of `0.50`.

   ```bash
   python -m 02_agentic_coding.control forward 0.8
   python -m 02_agentic_coding.control reverse 0.8
   python -m unittest -v 02_agentic_coding.test_control
   ```

   Expect `0.80` and `-0.80` in the starter previews, and two failures, `test_forward_above_limit` and `test_reverse_above_limit`.

2. Open the cloned folder in **OpenCode Desktop**. Choose **Plan** mode and ask:

   > Read 02_agentic_coding/control.py and 02_agentic_coding/test_control.py. Explain the two failing tests. Plan a change to clamp_speed that uses its supplied limit and preserves the sign. Keep the tests unchanged. Wait for review.

3. Review the plan, apply the edit with **Build**, and review the diff with `git diff -- 02_agentic_coding/control.py`. Rerun all three commands. Expect eight passing tests and previews with `0.50` and `-0.50`. These previews only print commands.
4. If you need to catch up, use the [reference implementation](solutions/clamp_speed.py) to replace just the `clamp_speed` function in `control.py`, then rerun the tests.
