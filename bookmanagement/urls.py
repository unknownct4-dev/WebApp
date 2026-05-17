from django.urls import path
from bookmanagement import views

app_name = 'bookmanagement'

urlpatterns = [
    # Old book claim form (kept for backward compatibility)
    path('claim/',      views.ClaimBookView.as_view(),        name='claim'),
    path('claimed/',    views.ClaimedBooksView.as_view(),     name='claimed'),
    path('enrollment/', views.EnrollmentSummaryView.as_view(), name='enrollment'),

    # New book submission (student submits 6 titles via AJAX POST)
    path('submit/',     views.SubmitBooksView.as_view(),      name='submit_books'),

    # Student polls their submission statuses (JSON)
    path('status/',     views.StudentBookStatusView.as_view(), name='book_status'),

    # Admin lifecycle actions
    path('admin/<int:pk>/received/',   views.AdminMarkReceivedView.as_view(),   name='admin_received'),
    path('admin/<int:pk>/processing/', views.AdminMarkProcessingView.as_view(), name='admin_processing'),
    path('admin/<int:pk>/claimable/',  views.AdminMarkClaimableView.as_view(),  name='admin_claimable'),
    path('admin/<int:pk>/claimed/',    views.AdminMarkClaimedView.as_view(),    name='admin_claimed'),
]
