# Project TODOs

- [ ] Reverse-engineer the BET Liferay portal API to fetch Insider Trading news and download PDFs.
- [ ] Document the BET API findings in `findings.md`.
- [ ] Integrate the working scraper logic into `app/scraper/client.py` and `app/features/insider_trading/tasks.py`.
- [ ] Write integration tests for the full pipeline.

---

## Prompt for the Next Copilot Agent 
**Copy and paste the text below into your next Copilot chat session:**

```text
Act as an Expert Python Web Scraper. Our project needs to download "Insider Trading" PDF documents from the Budapest Stock Exchange (bet.hu) website. However, the exact mechanics of their Liferay portal API are currently unknown to us.

Your task:
1. Create a standalone, throwaway Python script in the root directory (e.g., `bet_scraper_test.py`) to investigate and test the BET website. 
2. The target starting point is: `https://bet.hu/kereso?category=NEWS_NOT_BET`
3. Figure out how the Liferay portal manages sessions. You will likely need to:
   - Establish an initial `httpx` session to grab cookies (like `JSESSIONID`).
   - Use `BeautifulSoup` to find the Liferay auth token (often `p_auth` or `Liferay.authToken` in the DOM or window object) and the dynamic portlet URL (`p_p_id`, `p_p_lifecycle`, etc.).
   - Make the correct POST/GET request to retrieve the actual list of news items.
4. Figure out how to navigate from a news item to its actual attached PDF download URL.
5. **CRITICAL:** Implement generous `time.sleep()` calls, random delays, and use realistic browser `User-Agent` headers. Do NOT get my IP banned or rate-limited during your testing. Do not spam the server in tight loops.
6. Once your script successfully retrieves a PDF URL (or the file itself), analyze the mechanics.
7. Write down a detailed technical explanation of how the site works, the required headers, the session flow, and the JSON/HTML structures in a new file called `findings.md` in the root directory.

Use the `run_in_terminal` tool to iteratively run your `bet_scraper_test.py` script as you build it. Let me know when you have successfully written `findings.md`.
```