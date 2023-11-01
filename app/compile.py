import os,re
import subprocess
import py_compile


def c_compile_code(code):
    file = open("user_code.c", "w")
    file.write(code)
    file.close()

    # 컴파일 명령어
    compile_command = "gcc -o executable user_code.c"

    # 컴파일 실행
    result = subprocess.run(
        compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

    # 컴파일 결과에 따라 결과 반환
    if result.returncode == 0:
        output = subprocess.run(
            "./executable", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        output_str = output.stdout.decode("utf-8")
    else:
        output_str = result.stderr.decode("utf-8")

    os.remove("user_code.c")  # user_code.c 파일 삭제
    os.remove("executable")  # executable 파일 삭제

    return output_str


def cpp_compile_code(code):
    file = open("user_code.cpp", "w")
    file.write(code)
    file.close()

    # 컴파일 명령어
    compile_command = "g++ -o executable user_code.cpp"

    # 컴파일 실행
    result = subprocess.run(
        compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

    # 컴파일 결과에 따라 결과 반환
    if result.returncode == 0:
        output = subprocess.run(
            "./executable", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        output_str = output.stdout.decode("utf-8")
    else:
        output_str = result.stderr.decode("utf-8")

    os.remove("user_code.cpp")  # user_code.cpp 파일 삭제
    os.remove("executable")

    return output_str


def python_run_code(code):
    file = open("user_code.py", "w")
    file.write(code)
    file.close()

    try:
        py_compile.compile("user_code.py", doraise=True)

        # Python 코드 실행
        run_result = subprocess.run(
            ["python", "user_code.py"], capture_output=True, text=True
        )

        # 출력 결과 또는 오류 메시지 반환
        output_str = run_result.stdout or run_result.stderr
    except py_compile.PyCompileError as e:
        output_str = str(e)

    os.remove("user_code.py")  # user_code.py 파일 삭제

    return output_str


def java_compile_run_code(code):
    # 클래스 이름 추출
    class_name_match = re.search(r'public class (\w+)', code)
    if not class_name_match:
        return "Error: Could not find a public class declaration in the code."

    class_name = class_name_match.group(1)

    # 파일 생성
    file_path = f"{class_name}.java"
    with open(file_path, "w") as file:
        file.write(code)

    # 컴파일 명령어
    compile_command = f"javac {file_path}"

    # 컴파일 실행
    compile_result = subprocess.run(
        compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

    # 컴파일 결과에 따라 결과 반환
    if compile_result.returncode == 0:
        # 실행 명령어
        run_command = f"java {class_name}"

        # 실행
        run_result = subprocess.run(
            run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )

        # 실행 결과 반환
        if run_result.returncode == 0:
            output_str = run_result.stdout.decode("utf-8")
        else:
            output_str = run_result.stderr.decode("utf-8")
    else:
        output_str = compile_result.stderr.decode("utf-8")

    os.remove(file_path)  # .java 파일 삭제
    if os.path.exists(f"{class_name}.class"):
        os.remove(f"{class_name}.class")  # 컴파일된 클래스 파일 삭제

    return output_str


def grade_code(output_str, expected_output):
    if output_str.strip() == expected_output:
        return "정답입니다!"  # 정답인 경우
    else:
        return "오답입니다! ( ✋˙࿁˙ )"  # 오답인 경우
