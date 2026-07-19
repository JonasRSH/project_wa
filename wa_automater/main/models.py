from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator



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



only_digits = RegexValidator(r'^\d{11}$', 'Nur 11 Ziffern erlaubt.')


class TransitDocument(models.Model):
    t_number = models.CharField(max_length=30, primary_key=True)  # MRN-Nummer
    t_colli_quantity = models.IntegerField()
    t_weight = models.FloatField(null=True, blank=True)
    t_customs_office = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.t_number

    class Meta:
        verbose_name = "Transitdokument"
        verbose_name_plural = "Transitdokumente"


class Customs(models.Model):
    export_clearance = models.CharField(max_length=100, null=True, blank=True)
    eur1_certificate = models.CharField(max_length=100, null=True, blank=True)
    import_clearance = models.CharField(max_length=100, null=True, blank=True)
    transit_type = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Zollabfertigung"
        verbose_name_plural = "Zollabfertigungen"


class Shipment(models.Model):
    shipment_number = models.CharField(max_length=11, unique=True, validators=[only_digits])
    sender = models.CharField(max_length=200, null=True, blank=True)
    destination_country = models.CharField(max_length=2, null=True, blank=True)
    transit = models.ForeignKey(TransitDocument, null=True, blank=True, on_delete=models.SET_NULL)
    customs = models.ForeignKey(Customs, null=True, blank=True, on_delete=models.SET_NULL)
    abfahrt = models.ForeignKey(Abfahrt, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.shipment_number

    class Meta:
        verbose_name = "Sendung"
        verbose_name_plural = "Sendungen"


class Colli(models.Model):
    quantity = models.IntegerField()
    type = models.CharField(max_length=10, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='collis')

    class Meta:
        verbose_name = "Colli"
        verbose_name_plural = "Collis"