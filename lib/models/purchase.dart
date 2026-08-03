class Purchase {
  final int id;
  final int user;
  final String? userUsername;
  final int summary;
  final String? summaryTitle;
  final double amount;
  final String paymentMethod;
  final String status;
  final String? transactionId;
  final String createdAt;
  final String? completedAt;

  Purchase({
    required this.id,
    required this.user,
    this.userUsername,
    required this.summary,
    this.summaryTitle,
    required this.amount,
    required this.paymentMethod,
    required this.status,
    this.transactionId,
    required this.createdAt,
    this.completedAt,
  });

  factory Purchase.fromJson(Map<String, dynamic> json) {
    return Purchase(
      id: json['id'] ?? 0,
      user: json['user'] ?? 0,
      userUsername: json['user_username'],
      summary: json['summary'] ?? 0,
      summaryTitle: json['summary_title'],
      amount: double.tryParse(json['amount']?.toString() ?? '0') ?? 0.0,
      paymentMethod: json['payment_method'] ?? '',
      status: json['status'] ?? 'pending',
      transactionId: json['transaction_id'],
      createdAt: json['created_at'] ?? '',
      completedAt: json['completed_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user': user,
      'user_username': userUsername,
      'summary': summary,
      'summary_title': summaryTitle,
      'amount': amount,
      'payment_method': paymentMethod,
      'status': status,
      'transaction_id': transactionId,
      'created_at': createdAt,
      'completed_at': completedAt,
    };
  }

  bool get isCompleted => status == 'completed';
  bool get isPending => status == 'pending';
  bool get isFailed => status == 'failed';
}
