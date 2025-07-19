package com.novaticker;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private TextView newsTextView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        newsTextView = findViewById(R.id.newsTextView);
        Button refreshButton = findViewById(R.id.refreshButton);

        refreshButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                newsTextView.setText("최신 뉴스를 불러오는 중입니다...\n\n- 뉴스1: FDA 승인 소식\n- 뉴스2: 인수합병 발표\n- 뉴스3: 대형 투자 유치");
            }
        });
    }
}
