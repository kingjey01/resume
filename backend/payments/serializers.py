from rest_framework import serializers
from .models import Purchase, Service, Abonnement
from courses.models import Summary


class PurchaseSerializer(serializers.ModelSerializer):
    summary_title = serializers.CharField(source='summary.titre', read_only=True, default=None)
    user_username = serializers.CharField(source='user.username', read_only=True)
    service_name = serializers.CharField(source='service.nom', read_only=True, default=None)
    purchase_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Purchase
        fields = ['id', 'user', 'user_username', 'summary', 'summary_title',
                 'service', 'service_name', 'purchase_type',
                 'amount', 'payment_method', 'status', 'transaction_id', 
                 'created_at', 'completed_at']
        read_only_fields = ['user', 'transaction_id', 'completed_at']

    def get_purchase_type(self, obj):
        if obj.summary_id:
            return 'summary'
        elif obj.service_id:
            return 'subscription'
        return 'unknown'


class CreatePurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['summary', 'payment_method']
    
    def create(self, validated_data):
        user = self.context['request'].user
        summary = validated_data['summary']
        
        # Set amount from summary price
        validated_data['amount'] = summary.prix
        validated_data['user'] = user
        
        # Generate transaction ID
        import uuid
        validated_data['transaction_id'] = str(uuid.uuid4())
        
        return super().create(validated_data)


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'type', 'price', 'currency', 
                 'duree_mois', 'features', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class AbonnementSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.nom', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    montant = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)
    devise = serializers.CharField(source='service.currency', read_only=True)
    
    class Meta:
        model = Abonnement
        fields = ['id', 'user', 'user_username', 'service', 'service_name',
                 'date_debut', 'date_fin', 'status', 'auto_renew', 'progress',
                 'progress_percentage', 'montant', 'devise', 'created_at']
        read_only_fields = ['user', 'created_at', 'date_debut', 'date_fin', 'status']
    
    def get_progress_percentage(self, obj):
        """Calcule le pourcentage de progression de l'abonnement"""
        if obj.progress and obj.progress > 0:
            return min(obj.progress, 100)
        return 0
