from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    """사용자 모델을 위한 커스텀 매니저"""

    def create_user(self, user_id, user_name, user_email, password=None, **extra_fields):
        """일반 사용자를 생성합니다."""
        if not user_id:
            raise ValueError('The user_id must be set')
        if not user_email:
            raise ValueError('The user_email must be set')
        
        email = self.normalize_email(user_email)
        user = self.model(
            user_id=user_id,
            user_name=user_name,
            user_email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, user_name, user_email, password=None, **extra_fields):
        """관리자 권한을 가진 사용자를 생성합니다."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(user_id, user_name, user_email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """커스텀 사용자 모델"""
    user_id = models.CharField('로그인아이디', max_length=20, unique=True)
    user_name = models.CharField('사용자이름', max_length=20)
    user_phone = models.CharField('사용자전화번호', max_length=11, null=True, blank=True)
    user_email = models.EmailField('이메일주소', max_length=50, unique=True)
    
    is_staff = models.BooleanField('스태프 권한', default=False)
    is_active = models.BooleanField('활성 상태', default=True)
    created_at = models.DateTimeField('가입일', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['user_name', 'user_email']

    def __str__(self):
        return self.user_name or self.user_id

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"
        ordering = ['created_at']
