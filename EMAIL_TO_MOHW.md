# Email Template for Taiwan MOHW Client Registration

## Email in English

**To:** [Find contact at https://medstandard.mohw.gov.tw/ or https://emr.mohw.gov.tw/]

**Subject:** Urgent: SMART on FHIR Client Registration Request - Blood Pressure Management Application

---

Dear Taiwan MOHW FHIR Platform Team,

I am writing to request urgent client registration for our SMART on FHIR application that integrates with the Taiwan MOHW FHIR sandbox.

**Application Details:**
- **Name**: 血壓紅黃綠燈 (Blood Pressure Traffic Light System)
- **Purpose**: Post-ICH stroke blood pressure monitoring and management
- **Type**: Public web application (no client secret required)
- **Current Status**: Application is complete and deployed, awaiting client ID for OAuth integration

**Technical Requirements:**
- **Launch Type**: Provider Standalone Launch
- **Redirect URIs**:
  - Production: https://wftmufhir.streamlit.app/callback
  - Development: http://localhost:8501/callback
- **Required Scopes**:
  - openid
  - fhirUser
  - patient/Patient.read
  - patient/Observation.read
  - patient/Observation.write
  - patient/MedicationRequest.read
  - patient/MedicationAdministration.read
  - patient/Condition.read

**Target FHIR Server:**
https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir

**Urgency:**
We have a project deadline in 2 days and need the client_id to complete OAuth integration testing. The application is currently using Demo Mode but we would like to demonstrate live FHIR integration.

**Application Link:**
https://wftmufhir.streamlit.app/

**GitHub Repository:**
https://github.com/zeroR10B21022/WFtmuFHIR

Could you please provide:
1. A registered client_id for our application
2. Confirmation of the correct redirect_uri format (with or without /callback)
3. Any additional configuration requirements

If client registration requires additional documentation or approval process, please let me know what is needed and we will provide it immediately.

Thank you for your assistance.

Best regards,
[Your Name]
[Your Institution/Organization]
[Contact Email]
[Contact Phone]

---

## Email in Traditional Chinese (繁體中文)

**收件者:** [在 https://medstandard.mohw.gov.tw/ 或 https://emr.mohw.gov.tw/ 尋找聯絡方式]

**主旨:** 緊急：SMART on FHIR 客戶端註冊申請 - 血壓管理應用程式

---

尊敬的衛生福利部 FHIR 平台團隊：

我希望申請 SMART on FHIR 應用程式的客戶端註冊，以便與台灣衛福部 FHIR 沙盒整合。

**應用程式資訊：**
- **名稱**：血壓紅黃綠燈
- **目的**：腦出血術後血壓監測與管理
- **類型**：公開網頁應用程式（無需 client secret）
- **目前狀態**：應用程式已完成並部署，等待 client ID 進行 OAuth 整合

**技術需求：**
- **啟動類型**：Provider Standalone Launch（獨立啟動模式）
- **重定向 URI**：
  - 正式環境：https://wftmufhir.streamlit.app/callback
  - 開發環境：http://localhost:8501/callback
- **所需權限範圍**：
  - openid
  - fhirUser
  - patient/Patient.read
  - patient/Observation.read
  - patient/Observation.write
  - patient/MedicationRequest.read
  - patient/MedicationAdministration.read
  - patient/Condition.read

**目標 FHIR 伺服器：**
https://thas.mohw.gov.tw/v/r4/sim/WzIslilslilslkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwill0/fhir

**急件說明：**
我們的專案期限為 2 天後，需要 client_id 來完成 OAuth 整合測試。目前應用程式使用 Demo 模式運行，但我們希望能展示即時 FHIR 整合功能。

**應用程式連結：**
https://wftmufhir.streamlit.app/

**GitHub 儲存庫：**
https://github.com/zeroR10B21022/WFtmuFHIR

懇請提供：
1. 本應用程式的註冊 client_id
2. 確認正確的 redirect_uri 格式（是否需要 /callback 後綴）
3. 任何額外的配置要求

如果客戶端註冊需要額外文件或審批流程，請告知所需資料，我們會立即提供。

感謝您的協助。

敬祝
[您的姓名]
[您的機構/組織]
[聯絡電子郵件]
[聯絡電話]

---

## Where to Send

1. **Taiwan Medical Information Standards Platform**
   - Website: https://medstandard.mohw.gov.tw/
   - Look for "聯絡我們" (Contact Us) page

2. **MOHW FHIR Updates Page**
   - https://emr.mohw.gov.tw/myemr/Html/FHIR
   - Check for contact information or announcement section

3. **Alternative Contacts**
   - Taiwan Association for Medical Informatics (TAMI)
   - Your hospital/institution's IT department (if affiliated)
   - Academic advisor (if this is a research project)

## What to Do While Waiting

1. **Use Demo Mode** - This is production-ready and works now
2. **Prepare documentation** - Have all technical details ready if they respond
3. **Test alternative servers** - Consider SMART Health IT sandbox as backup

## Realistic Expectation

⚠️ **Important**: Healthcare organizations rarely respond within 2 days. Client registration typically requires:
- Security review (days to weeks)
- Legal approval (days to weeks)
- Business associate agreements (if applicable)

**Recommendation**: Present using Demo Mode for your deadline, continue OAuth integration separately.
