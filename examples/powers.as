set i = 2
set j = 1
while (j <= 10)
    echo "2 ** " + $j + " = " + $i
    @ i *= 2
    @ j++
end
