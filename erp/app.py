Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Install the latest PowerShell for new features and improvements! https://aka.ms/PSWindows

PS C:\WINDOWS\system32> Set-Location "C:\Users\Alienware\Documents\ERP-BERHAN"
>>
PS C:\Users\Alienware\Documents\ERP-BERHAN> if (!(Test-Path ".git")) { git init }
>>
>> # reset origin safely
>> $remotes = git remote
>> if ($remotes -match "^origin$") { git remote remove origin }
>> git remote add origin https://github.com/getson7070/ERP-BERHAN.git
>>
PS C:\Users\Alienware\Documents\ERP-BERHAN> git checkout -b fix/templates-cleanup 2>$null
>> if ($LASTEXITCODE -ne 0) { git checkout fix/templates-cleanup }
>>
D       templates/add_inventory.html
D       templates/add_report.html
D       templates/add_tender.html
D       templates/admin/workflows.html
D       templates/analytics/dashboard.html
D       templates/analytics/forecast.html
D       templates/analytics/report_builder.html
D       templates/auth/login.html
D       templates/auth/sso_totp.html
D       templates/auth/totp_enroll.html
D       templates/base.html
D       templates/base_auth.html
D       templates/calendar.html
D       templates/choose_login.html
D       templates/client_dashboard.html
D       templates/client_login.html
D       templates/client_registration.html
D       templates/compliance/signature_form.html
D       templates/crm/add.html
D       templates/crm/import.html
D       templates/crm/index.html
D       templates/customize_dashboard.html
D       templates/dashboard.html
D       templates/employee_dashboard.html
D       templates/employee_login.html
D       templates/employee_registration.html
D       templates/errors/401.html
D       templates/errors/403.html
D       templates/errors/404.html
D       templates/errors/500.html
D       templates/feedback.html
D       templates/finance/add.html
D       templates/finance/index.html
D       templates/help.html
D       templates/hr/add.html
D       templates/hr/index.html
D       templates/hr/performance.html
D       templates/hr/recruitment.html
D       templates/inventory.html
D       templates/inventory/add.html
D       templates/inventory/delete.html
D       templates/inventory/edit.html
D       templates/inventory/index.html
D       templates/inventory_out.html
D       templates/inventory_report.html
D       templates/kanban_board.html
D       templates/login.html
D       templates/maintenance_followup.html
D       templates/maintenance_report.html
D       templates/maintenance_request.html
D       templates/maintenance_status.html
D       templates/manufacturing/add.html
D       templates/manufacturing/index.html
D       templates/marketing.html
D       templates/marketing_report.html
D       templates/message.html
D       templates/my_approved_orders.html
D       templates/my_report.html
D       templates/offline.html
D       templates/order_status.html
D       templates/orders.html
D       templates/orders_list.html
D       templates/partials/batch_status.html
D       templates/partials/breadcrumbs.html
D       templates/partials/forecast_widget.html
D       templates/partials/help_tooltip.html
D       templates/partials/locale_switcher.html
D       templates/partials/messages.html
D       templates/partials/navbar.html
D       templates/partials/saved_views.html
D       templates/pharma/dashboard.html
D       templates/pharma_dashboard.html
D       templates/plugins/forecast.html
D       templates/plugins/index.html
D       templates/plugins/marketplace.html
D       templates/privacy.html
D       templates/procurement/add.html
D       templates/procurement/index.html
D       templates/projects/add.html
D       templates/projects/index.html
D       templates/promotion_report_activities.html
D       templates/promotion_report_sales.html
D       templates/put_order.html
D       templates/receive_inventory.html
D       templates/report_builder.html
D       templates/reports.html
D       templates/search_results.html
D       templates/status.html
D       templates/tenders.html
D       templates/tenders_list.html
D       templates/tenders_report.html
D       templates/upload_institutions.html
D       templates/user_management.html
Already on 'fix/templates-cleanup'
PS C:\Users\Alienware\Documents\ERP-BERHAN> # Ensure destinations exist
>> New-Item -ItemType Directory -Force -Path ".\erp\templates" | Out-Null
>> New-Item -ItemType Directory -Force -Path ".\erp\static"    | Out-Null
>>
>> # If top-level templates exist, copy them into erp\templates then delete top-level
>> if (Test-Path ".\templates") {
>>     Copy-Item -Recurse -Force ".\templates\*" ".\erp\templates\"  -ErrorAction SilentlyContinue
>>     Remove-Item -Recurse -Force ".\templates"
>> }
>>
>> # If top-level static exists, copy them into erp\static then delete top-level
>> if (Test-Path ".\static") {
>>     Copy-Item -Recurse -Force ".\static\*" ".\erp\static\"  -ErrorAction SilentlyContinue
>>     Remove-Item -Recurse -Force ".\static"
>> }
>>
PS C:\Users\Alienware\Documents\ERP-BERHAN>
