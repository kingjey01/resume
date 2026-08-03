enum PaymentMethodType {
  card,
  mobileMoney,
  rtlMoney,
}

class PaymentMethod {
  final PaymentMethodType type;
  final String name;
  final String icon;
  final String description;

  const PaymentMethod({
    required this.type,
    required this.name,
    required this.icon,
    required this.description,
  });

  static const List<PaymentMethod> availableMethods = [
    PaymentMethod(
      type: PaymentMethodType.mobileMoney,
      name: 'Mobile Money',
      icon: '📱',
      description: 'Orange Money, Airtel Money, Vodacom M-Pesa, Afrimoney',
    ),
  ];

  String get typeString {
    switch (type) {
      case PaymentMethodType.card:
        return 'card';
      case PaymentMethodType.mobileMoney:
        return 'mobile_money';
      case PaymentMethodType.rtlMoney:
        return 'mobile_money';
    }
  }
}

class PaymentDetails {
  final PaymentMethodType type;
  final Map<String, String> details;

  PaymentDetails({
    required this.type,
    required this.details,
  });

  // Pour carte bancaire
  factory PaymentDetails.card({
    required String cardNumber,
    required String expiryDate,
    required String cvv,
    required String holderName,
  }) {
    return PaymentDetails(
      type: PaymentMethodType.card,
      details: {
        'cardNumber': cardNumber,
        'expiryDate': expiryDate,
        'cvv': cvv,
        'holderName': holderName,
      },
    );
  }

  // Pour mobile money
  factory PaymentDetails.mobileMoney({
    required String phoneNumber,
    required String provider,
  }) {
    return PaymentDetails(
      type: PaymentMethodType.mobileMoney,
      details: {
        'phoneNumber': phoneNumber,
        'provider': provider,
      },
    );
  }

  // Pour RTL Money
  factory PaymentDetails.rtlMoney({
    required String phoneNumber,
    required String pin,
  }) {
    return PaymentDetails(
      type: PaymentMethodType.rtlMoney,
      details: {
        'phoneNumber': phoneNumber,
        'pin': pin,
      },
    );
  }
}
