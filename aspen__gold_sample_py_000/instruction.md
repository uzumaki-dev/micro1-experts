A participant on our eval platform says they can read other authors' task data through the API with just their normal participant key — gold patches, config, the works. Not sure exactly which endpoints they're hitting.

I need a test suite under `tests/exfiltration/` that catches the leak and locks down legitimate flows so a fix can't break them. `tests/test_smoke.py` shows the existing participant + admin flows — pin those with anti-overblock assertions.

**Rules:**
- Tests only. No changes to `taskhub/`.
- Use the same fixture helpers smoke_test.py uses.