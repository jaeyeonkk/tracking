$(document).ready(function () {
  $('#check-duplicate').click(function (e) { // 이벤트 핸들러 설정
    e.preventDefault(); // 기본 동작 중단
    var email = $('#username').val(); // '#username' 입력 필드 값을 가져옴

    // AJAX 요청 보냄
    $.ajax({
      url: '/check_duplicate', // 요청을 보낼 URL
      data: { username: email }, // 서버에 보낼 데이터
      type: 'POST', // 요청 방식
      success: function (response) {
        // 요청이 성공하면 응답 메시지 표시
        alert(response.message);
      },
      error: function (error) {
        // 요청이 실패하면 오류 정보 콘솔 출력
        console.log(error);
      },
    });
  });
});
