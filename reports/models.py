from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from .utiliyChoices import REPORT_TYPE_CHOICES, CATEGORY_CHOICES, STATUS_CHOICES, REACTION_CHOICES
import uuid

class Report(models.Model):
    # ID Unik
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relasi User (Guest/Member)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    
    # Data Input User
    type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    
    # PERBAIKAN 1: Ganti ImageField ke FileField
    # So that you can upload PDF/DOCX files to be parsed by our filtering system.
    attachment = models.FileField(upload_to='media/', blank=True, null=True)
    
    # AI Fields
    ai_summary = models.TextField(blank=True, null=True, help_text="Ringkasan otomatis by Gemini")
    sentiment_score = models.CharField(max_length=20, blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.author.username}"

    #Helper Methods for Template
    @property
    def total_upvotes(self):
        """Menghitung jumlah reaksi 'agree' (👍) sebagai total upvote"""
        return self.reactions.filter(type='agree').count()
    
    @property
    def total_reactions_count(self):
        """Menghitung total semua reaksi (termasuk sad, shock, dll)"""
        return self.reactions.count()

    def is_upvoted_by(self, user):
        """Cek apakah user tertentu sudah like/agree"""
        if not user.is_authenticated: return False
        return self.reactions.filter(user=user, type='agree').exists()

    # Auto Slug Generator
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            # Cut the UUID to 8 characters so that the slug isn't too long but remains unique.
            self.slug = f"{base_slug}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)


class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # related_name='reactions' It is important to be able to call via report.reactions.
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='reactions')
    
    # Tipe Reaction (agree, sad, support, dll)
    type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Constraint: One user can only give one reaction per report.
        unique_together = ('user', 'report')

    def __str__(self):
        return f"{self.user.username} reacted {self.type} on {self.report.id}"