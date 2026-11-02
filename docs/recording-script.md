# WorkNew review walkthrough

Record actual interactions with the 0.4.0 connected plugin in ChatGPT and Claude. Use only synthetic preferences and no real CV, contact information, credentials, other chats, or account details. Record the host window and returned results; do not substitute a simulated conversation or a terminal-only probe for a host test. Date the recording and identify the host and plugin version.

## Sequence

1. Show https://worknew.co/mcp and explain that WorkNew searches public, open assignments without a WorkNew login. Show the installed plugin and its search_jobs connection in the first host.
2. Run get-started with: “Ik deel liever geen cv. Ik zoek opdrachten als product owner.” Show that a CV is optional and the previous preference is reused.
3. Run the five positive cases from the manifest. Show the tool calls and a concise view of the results. Open one returned canonical job link. Make clear that current vacancies and counts can change.
4. Run the three negative cases. Show that the plugin does not apply, access private jobs, or transmit a CV or identifying information.
5. Repeat the relevant workflows in the second host. Do not claim identical outputs; verify the same intended behavior and public links.
6. Show the support/privacy links and end with the scope: public search, optional CV within the host, no applications or stored WorkNew profile.

Record the expected and actual behavior for each case in a dated evidence file. When a case fails, fix the package and repeat that case before recording the final walkthrough. Preserve the exact submitted ZIP hashes and GitHub commit alongside the evidence.

Upload the final recording to an approved public or reviewer-accessible location. Verify playback without the owner's session. Insert that real URL as `extensions.com.openai.review.demo_recording_url` in the source manifest, rebuild, and verify it survives in the ZIP. Do not treat the static MCP introduction page as the recording.
