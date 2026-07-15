# App Store Connect & Google Play Console — API Key Setup Guide

## App Store Connect (Apple)

### Step 1: Generate App Store Connect API Key
1. Go to [App Store Connect](https://appstoreconnect.apple.com/)
2. Navigate to **Users and Access** → **Integrations** → **App Store Connect API**
3. Click the **"+"** button to generate a new key
4. **Name**: `RealAICoach Analytics` (or any name you prefer)
5. **Access Level**: Select **Admin** or **Developer** (Admin gives full access to all analytics)
6. Click **Generate**
7. **IMPORTANT**: Download the `.p8` file immediately — Apple only lets you download it once
8. Note down:
   - **Key ID**: Shown in the key list (e.g., `ABC123DEFG`)
   - **Issuer ID**: Shown at the top of the API Keys page (e.g., `12345678-1234-1234-1234-123456789012`)

### Step 2: Get Your App's Bundle ID
1. In App Store Connect, go to **My Apps**
2. Select your app
3. Go to **App Information**
4. Note the **Bundle ID** (e.g., `com.realaicoach.app`)

### What to Provide to RealAICoach
Add these to your backend `.env` file:
```
ASC_ISSUER_ID=your-issuer-id-here
ASC_KEY_ID=your-key-id-here
ASC_PRIVATE_KEY_PATH=/path/to/AuthKey_XXXX.p8
ASC_APP_BUNDLE_ID=com.realaicoach.app
```

Or provide the private key content directly:
```
ASC_PRIVATE_KEY_CONTENT=-----BEGIN PRIVATE KEY-----\nMIGTAg...\n-----END PRIVATE KEY-----
```

---

## Google Play Console

### Step 1: Enable Google Play Developer API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project
3. Navigate to **APIs & Services** → **Library**
4. Search for **"Google Play Android Developer API"**
5. Click **Enable**

### Step 2: Create a Service Account
1. In Google Cloud Console, go to **IAM & Admin** → **Service Accounts**
2. Click **"+ Create Service Account"**
3. **Name**: `realaicoach-play-analytics`
4. **Role**: No role needed at this step
5. Click **Create and Continue** → **Done**

### Step 3: Generate a Key for the Service Account
1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** → **Create new key**
4. Select **JSON** format
5. Click **Create** — this downloads a `.json` file

### Step 4: Grant Access in Google Play Console
1. Go to [Google Play Console](https://play.google.com/console/)
2. Navigate to **Settings** → **API access**
3. Link the Google Cloud project you used above
4. Under **Service accounts**, find your service account
5. Click **Manage permissions**
6. Grant the following permissions:
   - **View app information and download bulk reports** (Read only)
   - **View financial data, orders, and cancellation survey responses**
   - **Reply to reviews**
7. Apply permissions to **all apps** or select specific apps
8. Click **Invite User** → **Save**

### Step 5: Get Your App's Package Name
1. In Google Play Console, go to your app
2. The package name is in the URL: `play.google.com/console/developers/.../app/{package_name}/...`
3. Example: `com.realaicoach.app`

### What to Provide to RealAICoach
Add these to your backend `.env` file:
```
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json
GOOGLE_PLAY_PACKAGE_NAME=com.realaicoach.app
```

Or provide the JSON content directly:
```
GOOGLE_PLAY_SERVICE_ACCOUNT_CONTENT={"type":"service_account","project_id":"...",...}
```

---

## Cloudflare CDN API (Optional)

### Step 1: Get Your API Token
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **My Profile** → **API Tokens**
3. Click **Create Token**
4. Use the **"Edit zone DNS"** template or create a custom token with:
   - **Zone**: Read
   - **Zone Settings**: Edit
   - **Cache Purge**: Purge
   - **Analytics**: Read
5. Click **Continue to Summary** → **Create Token**
6. Copy the token (shown only once)

### What to Provide to RealAICoach
```
CLOUDFLARE_API_TOKEN=your-api-token-here
CLOUDFLARE_ZONE_ID=your-zone-id-here
```

The Zone ID can be found on the **Overview** page of your domain in Cloudflare Dashboard.

---

## Summary: All Keys Needed

| Service | Keys Required |
|---------|--------------|
| App Store Connect | `ASC_ISSUER_ID`, `ASC_KEY_ID`, `ASC_PRIVATE_KEY_PATH` or `ASC_PRIVATE_KEY_CONTENT`, `ASC_APP_BUNDLE_ID` |
| Google Play Console | `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` or `GOOGLE_PLAY_SERVICE_ACCOUNT_CONTENT`, `GOOGLE_PLAY_PACKAGE_NAME` |
| Cloudflare CDN | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID` |

Once you provide these keys, I'll integrate them into the platform for real ASO data and CDN management.
