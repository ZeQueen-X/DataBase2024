DELIMITER $$
CREATE PROCEDURE get_stu_applying()
BEGIN
    SELECT student_id FROM management_student,management_dormapply where student_id = management_dormapply.applicant_id
    AND management_dormapply.status = 0 ;
end $$

DELIMITER ;