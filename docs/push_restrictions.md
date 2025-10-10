# Sandbox Push Limitations

This workspace runs inside an isolated container that has no network access and no
pre-configured Git remotes. Because of that, commits prepared here cannot be
pushed directly to `github.com/getson7070/ERP-BERHAN`.

To publish local work:

1. Clone the repository on a machine with internet access and the required
   credentials.
2. Add the GitHub remote if it is not already configured:

   ```bash
   git remote add origin https://github.com/getson7070/ERP-BERHAN.git
   ```

3. Push the branch (force-push only if you explicitly intend to overwrite the
   remote history):

   ```bash
   git push --force origin main
   ```

4. Verify the push on GitHub and ensure CI passes before deploying.

This process keeps the modernization work auditable while respecting the
sandbox's security boundaries.
