from django.db import models


class Zollamt(models.Model):
	ZOLLAMT_TYPEN = (
		("abgang", "Abgangszollstelle"),
		("grenz", "Grenzzollstelle"),
	)
	name = models.CharField(max_length=100)
	typ = models.CharField(max_length=10, choices=ZOLLAMT_TYPEN)

	def __str__(self):
		return f"{self.name} ({self.get_typ_display()})"
from django.db import models



class Abfahrt(models.Model):
	name = models.CharField(max_length=100)
	kennzeichen = models.CharField(max_length=20)
	anhaenger = models.CharField(max_length=20, blank=True, null=True)

	def __str__(self):
		if self.anhaenger:
			return f"{self.name} ({self.kennzeichen} / {self.anhaenger})"
		return f"{self.name} ({self.kennzeichen})"
