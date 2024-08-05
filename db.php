<?php
$contents = file_get_contents('php://input');
/* Тусынавыхи */
/*pg_connect("host=ec2-54-235-248-185.compute-1.amazonaws.com
                                    port=5432 dbname=d610l2cahre9nd
                                    user=hkxuydhzgnfxtr
                                    password=123")
            or die('Could not connect: ' . pg_last_error());
*/
/*ТГ бот partyfind*/
pg_connect("host=ec2-54-75-224-168.eu-west-1.compute.amazonaws.com
                                    port=5432 dbname=dbb58oc8ebc98t
                                    user=ittflvghllwmmh
                                    password=123")
            or die('Could not connect: ' . pg_last_error());
$q = "INSERT INTO logs (contents) values ('".$contents."')";
pg_query($q);
?>