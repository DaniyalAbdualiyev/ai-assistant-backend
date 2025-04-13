# Manual Render Deployment Instructions

If your Render project is not set up for automatic deployments, follow these steps to manually deploy your changes:

1. **Log in to Render**: Go to [https://dashboard.render.com](https://dashboard.render.com) and sign in to your account.

2. **Navigate to Your Web Service**: Find and click on your AI Assistant Backend web service in the dashboard.

3. **Trigger Manual Deploy**: 
   - In the web service dashboard, look for the "Manual Deploy" button or dropdown
   - Select "Deploy latest commit" or a similar option
   - Render will pull the latest code from your GitHub repository and start the deployment process

4. **Monitor Deployment**:
   - You can monitor the deployment progress in the Render dashboard
   - The dashboard will show logs and deployment status
   - A successful deployment will show a "Live" status

5. **Verify Your Changes**:
   - Once deployment is complete, test your API endpoints
   - Use the frontend application or tools like Postman to verify the registration endpoint works correctly
   - Check for any errors in the Render logs

6. **Troubleshooting**:
   - If the deployment fails, check the Render logs for error messages
   - Common issues include failed build processes or database connection problems
   - You can make additional fixes, commit, and deploy again if needed

Your changes should now be live on your Render deployment, and the registration endpoint should work correctly with the fixed code and database schema! 