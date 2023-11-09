const alertSound = document.getElementById('alertSound');


// 모달창 가져오기
var modal = document.getElementById('myModal');
var btn = document.getElementById("startButton");
var span = document.getElementsByClassName("close")[0];


// 사용자가 모달창 외부를 클릭하면 모달창을 닫음
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}


// 사용자가 X 버튼을 클릭하면 모달창을 닫음
span.onclick = function() {
    modal.style.display = "none";
}


// 트래킹 시작 버튼을 클릭하면 트래킹 함수를 호출
btn.onclick = function() {
    modal.style.display = "none";
    startTracking();
}


function startTracking() {
    // 1초마다 얼굴 상태 확인
    setInterval(checkFaceCount, 1000);
}


$(function() {
  // 아이 트래킹 섹션에 드래그 가능하게 설정
  $("#draggableEyeTracking").draggable();
});


// 경고창 발생 횟수를 저장할 객체
const alertCounts = {
  faceMany: 0,
  faceEmpty: 0,
  faceChange: 0,
  headRotation: 0
};


function checkFaceCount() {
  fetch("http://127.0.0.1:5000/face_info")
  .then(response => response.json())
  .then(data => {
    console.log(data);
    if (data.face_count > 1) {
      alert('얼굴 많아!');
      alertCounts.faceMany++;
    }
    if (data.no_face_for >= 5) {
      alert('어디갔어!');
      alertCounts.faceEmpty++;
    }
    if (data.face_changed) {
      alert('사람이 변했어!');
      alertCounts.faceChange++;
    }
    if (data.head_rotation_alert) {
      alert('고개가 회전되었습니다!');
      alertCounts.headRotation++;
    }
    
    const alertSound = document.getElementById('alertSound');
    
    // 눈이 감겼을 때(true), 소리를 재생
    if (data.alert_playing) {
      alertSound.play();
    } 
    // 눈이 뜨였을 때(false), 소리를 정지
    else {
      alertSound.pause(); // 현재 재생 중인 소리를 멈춤
      alertSound.currentTime = 0; // 소리를 처음부터 다시 시작할 수 있도록 현재 시간을 0으로 설정한다.
    }
  });
}


setInterval(checkFaceCount, 1000);  // Check every 1000 milliseconds (1 second)


// 페이지 로드 시 모달창 표시
window.onload = function() {
    modal.style.display = "block";
}


//     $("#submit").click(function() {
//       if (!isCodePresent()) {
//         alert("코드를 작성해주세요.");
//         return;
//       }

//   // alertCounts 객체에 담긴 경고창 발생 횟수를 서버로 보낼 데이터에 추가
//   var submissionData = {
//     code: $("textarea[name='code']").val(),
//     language: $("select[name='language']").val(), // 언어 선택 값을 추가
//     face_many: alertCounts.faceMany,
//     face_empty: alertCounts.faceEmpty,
//     face_change: alertCounts.faceChange,
//     head_rotation: alertCounts.headRotation
//   };

//   $.ajax({
//     type: "POST",
//     url: "/submit",
//     data: submissionData,
//     success: function(result) {
//       $("#grade-box").html("<pre>" + result + "</pre>");
//       $("#grade-box").removeClass("hidden");
//     }
//   });
// });


const header = document.querySelector("header");


window.addEventListener("scroll", function() {
  header.classList.toggle("sticky", window.scrollY > 80);
});

$(document).ready(function() {
  var isCodeExecuted = false; // 코드가 실행되었는지 확인하는 flag

  function isCodePresent() {
    return $("textarea[name='code']").val().trim() !== "";
  }

  $("form").submit(function(e) {
    e.preventDefault();

    // 코드가 작성되었는지 확인
    if (!isCodePresent()) {
      alert("코드를 작성해주세요.");
      return;
    }

    $.ajax({
      type: "POST",
      url: "/compile",
      data: $(this).serialize(),
      success: function(result) {
        $("#result").html("<pre>" + result + "</pre>");
        isCodeExecuted = true; // 코드가 실행된 후 flag를 true로 설정
      }
    });
  });

  
  $("#submit").click(function() {
    // 코드가 작성되었는지 확인
    if (!isCodePresent()) {
      alert("코드를 작성해주세요.");
      return;
    }
    $.ajax({
      type: "POST",
      url: "/submit",
      data: {
        code: $("textarea[name='code']").val(),
        language: $("select[name='language']").val() // 언어 선택 값을 추가
      },
      success: function(result) {
        $("#grade-box").html("<pre>" + result + "</pre>");
        $("#grade-box").removeClass("hidden"); // 박스를 보이도록 클래스 제거
      }
    });
  });


  $("#save_code").click(function() {
    var codeContent = $("textarea[name='code']").val().trim();

    // 코드가 작성되었는지 확인
    if (codeContent === "") {
      alert("코드를 작성해주세요.");
      return;
    }

    // 코드가 실행되었는지 확인
    if (!isCodeExecuted) {
      alert("코드를 실행해주세요.");
      return;
    }

    // 결과를 가져오기
    var compileResult = $("#result pre").text();

    $.ajax({
      type: "POST",
      url: "/save_code",
      data: {
        q_id: '{{ q_list.q_id }}',
        code_content: codeContent,
        language: $("select[name='language']").val(),
        compile_result: compileResult
      },
      success: function(result) {
        alert("코드가 저장되었습니다.");
      },
      error: function(error) {
        alert("코드 저장 중 문제가 발생했습니다.");
      }
    });
  });
});