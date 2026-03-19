from django.db import models
from django.contrib.auth.models import User


class Zollamt(models.Model):
	ZOLLAMT_TYPEN = (
		("abgang", "Abgangszollstelle"),
		("grenz", "Grenzzollstelle"),
	)
	name = models.CharField(max_length=100)
	typ = models.CharField(max_length=10, choices=ZOLLAMT_TYPEN)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return f"{self.name} ({self.get_typ_display()})"

	class Meta:
		verbose_name = "Zollamt"
		verbose_name_plural = "Zollämter"


class Abfahrt(models.Model):
	name = models.CharField(max_length=100)
	kennzeichen = models.CharField(max_length=20)
	anhaenger = models.CharField(max_length=20, blank=True, null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		if self.anhaenger:
			return f"{self.name} ({self.kennzeichen} / {self.anhaenger})"
		return f"{self.name} ({self.kennzeichen})"

	class Meta:
		verbose_name = "Abfahrt"
		verbose_name_plural = "Abfahrten"
