from rest_framework import serializers


class RiderInput(serializers.Serializer):
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=160)
    kind = serializers.ChoiceField(choices=["employee", "independent"])


class DeliveryMutation(serializers.Serializer):
    revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=["assign", "stage", "destination", "sharing"])
    rider_id = serializers.UUIDField(required=False, allow_null=True)
    stage = serializers.ChoiceField(choices=["ready", "out_for_delivery", "delivered", "cancelled"], required=False)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    sharing = serializers.BooleanField(required=False)

    def validate(self, attrs):
        required = {"assign": ["rider_id"], "stage": ["stage"], "destination": ["latitude", "longitude"], "sharing": ["sharing"]}[attrs["action"]]
        for key in required:
            if key not in attrs:
                raise serializers.ValidationError({key: "This field is required for this action."})
        return attrs


class LocationInput(serializers.Serializer):
    revision = serializers.IntegerField(min_value=1)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField()
    captured_at = serializers.DateTimeField()
