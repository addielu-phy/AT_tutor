/* AT_tutor 雲端設定（Firebase）
   高醫 115 物理及化學學生交卷同步與教師端跨裝置統計。
   瀏覽器 Firebase Web config 為公開識別資訊；資料存取由 Auth 與 Firestore Rules 保護。 */
window.CLOUD = {
  enabled: true,
  teacherEmail: "cylcphychem@gmail.com",   // 須與 Firestore 安全規則中的 Email 一致
  config: {
    apiKey: "AIzaSyDo_v6NF4lkmd-WEe6CVvweth4Y-O1-kv0",
    authDomain: "cap-review-c2f24.firebaseapp.com",
    projectId: "cap-review-c2f24",
    storageBucket: "cap-review-c2f24.firebasestorage.app",
    messagingSenderId: "875329911054",
    appId: "1:875329911054:web:e446db5ea5f663a0ce3f5f"
  }
};
